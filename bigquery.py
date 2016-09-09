# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import os
from datetime import datetime
from time import sleep, time

from errbot import botcmd, BotPlugin, arg_botcmd

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from charts import interval, generate_timeseries_linechart, generate_barchart
from charts.line import Collection, Line


def get_ts():
    now = datetime.now()
    return '%s.%d' % (now.strftime('%Y%m%d-%H%M%S'), now.microsecond)

class BigQuery(BotPlugin):
    def activate(self):
        super().activate()
        if 'queries' not in self:
            self['queries'] = []
        self.gc = self.get_plugin('GoogleCloud')
        self.credentials = self.gc.credentials
        self.bigquery = build('bigquery', 'v2', credentials=self.credentials)

    def project(self):
        if not self.is_activated:
            return None

        if 'project' not in self.gc:
            raise Exception('You need to define a project with !project set first.')
        return self.gc['project']

    def bucket(self):
        if 'bucket' not in self.gc:
            raise Exception('No Bucket set.')
        return self.gc['bucket']

    @botcmd
    def bq_datasets(self, msg, args):
        """List the datasets from the project."""
        datasets = self.bigquery.datasets()
        response = datasets.list(projectId=self.project()).execute()
        for dataset in response['datasets']:
            yield '%s' % dataset['datasetReference']['datasetId']

    @staticmethod
    def extract_fields(schema_fields):
        result = []
        for field in schema_fields:
            typ = field['type']
            name = field['name']
            if typ == 'TIMESTAMP':
                result.append((name,
                               lambda s: datetime.fromtimestamp(float(s)).strftime('%Y-%m-%d %H:%M:%S')
                               ))
            elif typ == 'STRING':
                result.append((name,
                               lambda s: s))
            else:
                result.append((name, str))
        return result


    @botcmd
    def bq_addquery(self, msg, args:str):
        """
        Stores a query and assigns it a number.
        """
        with self.mutable('queries') as queries:
            queries.append(args)
        return "Your query has been stored, you can execute it with !bq %i." % (len(queries) - 1)

    @botcmd
    def bq_delquery(self, msg, args: str):
        """
        Removes a stored query.
        """
        with self.mutable('queries') as queries:
            del queries[int(args)]
        return "%i queries have been defined." % len(queries)

    @botcmd
    def bq_queries(self, msg, args:str):
        return '\n\n'.join("%i: %s" % (i, q) for i, q in enumerate(self['queries']))

    @botcmd
    def bq(self, msg, args: str):
        """Start a new query."""
        #  if it is a number, assume it is an index for the saved queries.
        try:
            args = self['queries'][int(args)]
        except ValueError:
            pass

        if not args:
            return 'Usage: !bq QUERY_OR_QUERY_INDEX\nYou can save a query with !bq addquery'

        query = args.strip()

        for response, feedback in self.sync_bq_job(query):
            if response:
                break
            yield feedback

        fields = self.extract_fields(response['schema']['fields'])

        i = 0
        rows = []
        for row in response['rows']:
            rows.append([field[1](value['v']) for field, value in zip(fields, row['f'])])
            i += 1
            if i == 10:
                break
        header = '| ' + ' | '.join(field[0] for field in fields) + ' |\n'
        values = '\n'.join('| ' + ' | '.join(v for v in row) + ' |' for row in rows)
        return header + values

    def sync_bq_job(self, query: str):
        """
        Execute Synchronously the given query on BigQuery.
        :param query: the bq query
        :return: tuple of the response or None, Feedback if None.
        """
        start_time = time()
        jobs = self.bigquery.jobs()
        response = jobs.query(projectId=self.project(), body={'query': query}).execute()
        job_id = None
        while 'jobComplete' in response and not response['jobComplete']:
            job_id = response['jobReference']['jobId']
            yield None, 'BigQuery job "%s" is in progress ... %0.2fs' % (job_id, time()-start_time)
            sleep(5)
            response = jobs.get(projectId=self.project(), jobId=job_id).execute()

        if job_id:
            yield jobs.getQueryResults(projectId=self.project(), jobId=job_id).execute(), ''
        else:
            yield response, ''

    @arg_botcmd('query', type=str)
    @arg_botcmd('--index', dest='index', type=str, default='0')
    @arg_botcmd('--values', dest='values', type=str)
    def bq_chart(self, msg, query: str, index: str, values: str):
        """
        Start a new query and graph the result.
        By default it will autoguess the graph type depending on the first column.
        Otherwise you can specify the column index or name of the index with --index and the value columns to graph
        with --values separated with comma.
        """
        #  if it is a number, assume it is an index for the saved queries.
        try:
            query = self['queries'][int(query)]
        except ValueError:
            pass

        if not query:
            yield 'Usage: !bq chart [--index nb_or_name] [--values nb_or_name,...] QUERY_OR_QUERY_INDEX\n' \
                   'You can save a query with !bq addquery'

        for response, feedback in self.sync_bq_job(query):
            if response:
                break
            yield feedback

        schema_fields = response['schema']['fields']

        try:
            index_index = int(index)
        except ValueError:
            index_index = next(i for i, field in enumerate(schema_fields) if field['name'] == index)

        if values:
            value_strs = values.split(',')
            try:
                values_indices = [int(value) for value in value_strs]
            except ValueError:
                values_indices = [i for i, field in enumerate(schema_fields) if field['name'] in value_strs]
        else:
            values_indices = list(range(1, len(schema_fields)))  # assume all the columns are relevant

        filename = '%s.%s.png' % (self.project(), get_ts())
        output = os.path.join(self.gc.outdir, filename)

        if schema_fields[index_index]['type'] == 'TIMESTAMP':
            # Generate a timeseries graph.

            # makes a "pivot" for the data to be graphable.
            xs = []  # xs is constant for all the series.
            series = [[]] * len(values_indices)
            for row in response['rows']:
                y = 0
                for i, value in enumerate(row['f']):
                    if i in values_indices:
                        series[y].append(float(value['v']))
                        y += 1
                xs.append(datetime.fromtimestamp(float(row['f'][index_index]['v'])))

            start, end = xs[0], xs[-1]

            collection = Collection(lines=[Line(schema_fields[values_indices[i]]['name'], xs, ys) for i, ys in enumerate(series)],
                                    title=query,
                                    start=start,
                                    end=end)

            generate_timeseries_linechart(
                collection=collection,
                time_interval_display=interval.Guess(start, end),
                outfile=output,
            )

            yield self.save_image(filename, output, response)['mediaLink']
        elif schema_fields[index_index]['type'] == 'STRING':
            labels = []
            values = []
            for row in response['rows']:
                labels.append(row['f'][index_index]['v'])
                values.append(row['f'][1]['v'])
            with open(output, 'rb') as source:
                generate_barchart(title=filename, ylabel='', labels=labels, values=values, outfile=source)
            yield self.save_image(filename, output, response)['mediaLink']
        else:
            yield "The index column is of type %s which is not compatible for a graph: " \
                   "it should be either a TIMESTAMP or a STRING." % schema_fields[index_index]['type']

    def save_image(self, filename, output, response):
        with open(output, 'rb') as source:
            media = MediaIoBaseUpload(source, mimetype='image/png')
            response = self.gc.storage.objects().insert(bucket=self.bucket(),
                                                        name=filename,
                                                        media_body=media,
                                                        predefinedAcl='publicRead').execute()
        return response