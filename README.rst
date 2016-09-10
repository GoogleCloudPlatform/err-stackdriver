.. image:: https://img.shields.io/travis/GoogleCloudPlatform/err-gcloud/master.svg
   :target: https://travis-ci.org/GoogleCloudPlatform/err-gcloud/

.. image:: https://img.shields.io/badge/License-Apache_v2-green.svg
   :target: http://www.apache.org/licenses/LICENSE-2.0 
   :alt: License

.. image:: https://img.shields.io/badge/gitter-join%20chat%20%e2%86%92-brightgreen.svg
   :target: https://gitter.im/googlecloudplatform/err-gcloud?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
   :alt: join the chat at https://gitter.im/googlecloudplatform/err-gcloud

Google Cloud ChatOps plugin for Errbot
======================================

This plugin allows you to connect expose commands for your team in a Slack or Hipchat channel.
`More information about Errbot <http://errbot.io>`_.

For example, this is a screenshot showing the bigquery feature where you can execute or graph a saved query directly
from Slack.

.. image:: https://raw.githubusercontent.com/GoogleCloudPlatform/err-gcloud/master/docs/imgs/bigquery.png

Quickstart
----------

First you need to install Errbot, you can `follow this documentation <http://errbot.io/en/latest/user_guide/setup.html>`_.

It is recommended to use a GCE VM for that.

Then you'll need to install this plugin on your Errbot instance doing `!repos install err-gcloud`, you can do that by talking to your bot locally with `errbot -T`. 

The plugin will need a service account .json key in the data directory of errbot renamed as `servacc.json`.

Once evrything is setup, you can connect your bot to your Slack channel following `this documentation <http://errbot.io/en/latest/user_guide/configuration/slack.html>`_.

Contributing
------------

Contributions to this plugin are always welcome and highly encouraged.

See `err-gcloud`'s `CONTRIBUTE <CONTRIBUTE.md>`_ documentation.

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. See `Code of Conduct <CODE_OF_CONDUCT.md>`_ for more information.

License
-------

Apache 2.0 - See `LICENSE <LICENSE>`_ for more information.
