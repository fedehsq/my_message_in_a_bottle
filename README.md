# Message in a bottle

[![Build Status](https://app.travis-ci.com/ManfredoFac/HW2.svg?token=sCUbEzotwbjEpdHdvWDb&branch=main)](https://app.travis-ci.com/ManfredoFac/HW2) [![Coverage Status](https://coveralls.io/repos/github/ManfredoFac/HW2/badge.svg?branch=main&t=gy6EPP)](https://coveralls.io/github/ManfredoFac/HW2?branch=main)

## Description

"**MyMessageInABottle** might seem at first glance
simply like another messaging app, like many others. WRONG.\
MyMessageInABottle is a time capsule where each user can keep messages, safeguard them, and send them only to decide later when
the recipient will be able to open them. Whether it’s at a specific time
on that same day, weeks later, or even years later. What matters is that
the message cannot be changed or deleted. Even if you uninstall the
app. And it will reach its destination. It’s important.\
There are choices
to be made, and you need to take your time."

## Tools

To develeop this application, several software/framework have been used:

1. [Flask](https://palletsprojects.com/p/flask/) is a lightweight WSGI web application framework. It is designed to make getting started quick and easy, with the ability to scale up to complex applications.

2. [Jinja](https://palletsprojects.com/p/jinja/) is one of the most used template engines for Python. It is inspired by Django's templating system but extends it with an expressive language that gives template authors a more powerful set of tools.

3. [Celery](https://docs.celeryproject.org/en/stable/) is a simple, flexible, and reliable distributed system to process vast amounts of messages, while providing operations with the tools required to maintain such a system.
It’s a task queue with focus on real-time processing, while also supporting task scheduling.

4. [SQLAlchemy](https://www.sqlalchemy.org/) is the Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.

5. [Travis CI](https://www.travis-ci.com/) is the simplest way to test and deploy your projects. Easily sync your projects with Travis CI and you’ll be testing your code in minutes.

6. [Coveralls](https://coveralls.io/) "DELIVER BETTER CODE" helps you to deliver code confidently by showing which parts of your code aren’t covered by your test suite.

### [For more details](https://github.com/ManfredoFac/HW2/blob/main/message_in_a_bottle.pdf)

## Functionalities

The web app developed provides the following functionalities shown with the user stories.
![User stories](https://github.com/ManfredoFac/HW2/blob/main/user_stories.png)

## Instructions

1. Open the project in your IDE.
2. From IDE terminal, or normal Ubuntu/MacOS terminal execute the command `virtualenv venv` inside project root.
3. Now, you have to activate it, by executing the command `source venv/bin/activate`.
4. You have to install all requirements, let's do that with `pip install -r requirements.txt`.

**Perfect!** now you can run flask application!

<span style="color:orange">WARNING:</span> each time that you open a new terminal session you have
to execute the step 3.

### Run the application

If you want to run the application, you can use the script `run.sh` by typing `bash run.sh`,
or you can set these environment variables:

```
FLASK_DEBUG=1
FLASK_ENV=development
```
Then run
```
celery -A monolith.background worker -l debug
celery -A monolith.background beat -l debug
```
## Authors

* [Federico Bernacca](https://github.com/fedehsq)

* [Paola Petri](https://github.com/paolapetri)

* [Nicolò Pierami](https://github.com/pieramin)

* [Manfredo Facchini](https://github.com/ManfredoFac)

* [Francesco Kotopulos De Angelis](https://github.com/dookie182)
