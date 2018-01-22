# Server side DataTables plugin for a Flask and MongoDB application with no ORM

I needed to implement a very basic table with data that would be reported in constantly from multiple devices within Spain, and I decided to go with Flask and MongoDB (both because they wanted something quick, and because I felt like learning those two would allow me to easily add more stuff on top further down the road).

Issue was, I couldn't find any server side plugins for this combination, only one for when you use an ORM, which I wanted to avoid. The best I could find [was a very old class](https://gist.github.com/illerucis/4586359) (in which this is based) that used to work with early versions of DataTables, but not the most recent one.

So I decided to modify it and make it work with the newer versions so I could have a somewhat general solution that I could use in other projects as well.


## How to use

First you need to have both [Flask](http://flask.pocoo.org/docs/latest/) and [pymongo](https://api.mongodb.com/python/current/) installed in either your Python path or your virtual environment, whichever you're going to use.

Then you need your Flask application. Let's assume this is your application file hierarchy:

'''

'''
