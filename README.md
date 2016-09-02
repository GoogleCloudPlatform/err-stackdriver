Google Cloud ChatOps plugin for Errbot
======================================

This plugin allows you to connect expose commands for your team in a Slack channel.

Quickstart
----------

First you need to install Errbot, you can [follow this documentation](http://errbot.io/en/latest/user_guide/setup.html).
It is recommended to use a GCE VM for that.

Then you'll need to install this plugin on your Errbot instance doing `!repos install err-gcloud`, you can do that by talking to your bot locally with `errbot -T`. 

The plugin will need a service account .json key in the data directory of errbot renamed as `servacc.json`.

Once evrything is setup, you can connect your bot to your Slack channel following [this documentation](http://errbot.io/en/latest/user_guide/configuration/slack.html).

Contributing
------------

Contributions to this plugin are always welcome and highly encouraged.

See `err-gcloud`'s [CONTRIBUTE] documentation.

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. See [Code of Conduct][code-of-conduct] for more information.

License
-------

Apache 2.0 - See [LICENSE] for more information.