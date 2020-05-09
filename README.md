# Amplium
Python-based proxy for multiple Selenium Grid Hubs.

About Amplify
=============
Amplify builds innovative and compelling digital educational products that empower teachers and students across the country. We have a long history as the leading innovator in K-12 education - and have been described as the best tech company in education and the best education company in tech. While others try to shrink the learning experience into the technology, we use technology to expand what is possible in real classrooms with real students and teachers.

Learn more at https://www.amplify.com

What Does Amplium Do?
=====================

Amplium is intended to make it easier to manage multiple Selenium Grid Hubs by removing the some of the difficulties of working with multiple Selenium Grid Hubs. Primarily, Amplium acts as a proxy to mutliple Selenium Selenium Grid Hubs, allowing your tests to seamlessly split between multiple other Selenium Grid Hubs. Additionally, instances of Amplium are stateless, so it is possible to scale Amplium up and down without affecting your running tests.

Quick Start
===========
```bash
pip install -e .
pip install -r requirements.pip
AMPLIUM_CONFIG=config/example.yml python amplium/app.py
```

You'll now have an Amplium server running on `http://0.0.0.0:8081/`.

You can check out the `/status` endpoint and see any actively running sessions.

You can pass `http://0.0.0.0:8081/proxy` as your new Selenium Grid Hub, and now you're Selenium tests will be distributed over multiple Selenium Grid Hubs via Amplium.

Getting Started
===============
Prerequisites
-------------
Amplium requires the following:
```
tox>=2.9.1
python >= 3.7
```

Running Tests
-------------
Amplium uses tox as its test runner. To run the linters and unit tests, simply run:
```bash
tox
```

Configuration
-------------
Amplium's configuration comes primarily from a single YAML file. Amplium looks for this file in `/etc/amplium/config.yml` by default. However, this location can be overridden by setting the `AMPLIUM_CONFIG` environment variable. An example of this configuration file is provided in this repo.

Stack
-----
Amplium uses Swagger and Connexion to expose a WSGI-compatible application. Amplium uses DynamoDB for storing it's state information and Zookeeper for discovering Selenium Grid Hubs. For deployment, Amplium is intended to be deployed as a WSGI application behind Apache or another service that can serve WSGI applications.

Responsible Disclosure
======================
If you have any security issue to report, contact project maintainers privately.
You can reach us at <github@amplify.com>

Contributing
============
We welcome pull requests! For your pull request to be accepted smoothly, we suggest that you:
1. For any sizable change, first open a GitHub issue to discuss your idea.
2. Create a pull request.  Explain why you want to make the change and what it’s for.
We’ll try to answer any PR’s promptly.
