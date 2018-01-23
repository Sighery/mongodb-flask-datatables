# Server side DataTables plugin for a Flask and MongoDB application with no ORM

I needed to implement a very basic table with data that would be reported in constantly from multiple devices within Spain, and I decided to go with Flask and MongoDB (both because they wanted something quick, and because I felt like learning those two would allow me to easily add more stuff on top further down the road).

Issue was, I couldn't find any server side plugins for this combination, only one for when you use an ORM, which I wanted to avoid. The best I could find [was a very old class](https://gist.github.com/illerucis/4586359) (in which this is based) that used to work with early versions of DataTables, but not the most recent one.

So I decided to modify it and make it work with the newer versions so I could have a somewhat general solution that I could use in other projects as well.

---

## How to use

First you need to have both [Flask](http://flask.pocoo.org/docs/latest/) and [pymongo](https://api.mongodb.com/python/current/) installed in either your Python path or your virtual environment, whichever you're going to use.

Then you need your Flask application. Let's assume this is your **application's file hierarchy**:

```
app
├── datatables.py
├── main.py
├── static
│   ├── bootstrap.min.css
│   ├── bootstrap.min.js
│   ├── jquery.dataTables.min.css
│   ├── jquery.dataTables.min.js
│   ├── jquery.min.js
│   ├── main.css
│   ├── main.js
│   ├── sort_asc.png
│   ├── sort_both.png
│   └── sort_desc.png
└── templates
	└── index.html
```

Assume we have an application about devices, each with at max 3 temperature sensors, reporting that data to your MongoDB database either directly or through some API.

A **record in the database** might look something like this, for instance:

```
{
	'id': 'Device1',
	'ip': '10.112.113.114',
	'sensors': [
		{
			'id': 1,
			'reading': 28.091
		},
		{
			'id': 2,
			'reading': 12.599
		},
		{
			'id': 3,
			'reading': 23.417
		}
	],
	'temp_cpu': 44.312,
	'date': Date("2018-01-01T01:02:03Z")
}
```

Your **index.html** file would have a simple table such as:

```
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8"/>
	<title>Example</title>
	<!-- jQuery -->
	<script src="{{ url_for('static', filename='jquery.min.js') }}" type="text/javascript"></script>
	<!-- /jQuery -->
	<!-- DataTables -->
	<script src="{{ url_for('static', filename='jquery.dataTables.min.js') }}" type="text/javascript"></script>
	<link href="{{ url_for('static', filename='jquery.dataTables.min.css') }}" rel="stylesheet" type="text/css"/>
	<!-- /DataTables -->
	<!-- Bootstrap -->
	<script src="{{ url_for('static', filename='bootstrap.min.js') }}" type="text/javascript"></script>
	<link href="{{ url_for('static', filename='bootstrap.min.css') }}" rel="stylesheet" type="text/css"/>
	<!-- /Bootstrap -->
	<!-- App styles -->
	<link href="{{ url_for('static', filename='main.css') }}" rel="stylesheet" type="text/css"/>
	<!-- /App styles -->
</head>
<body>
	<table id="example-table">
		<thead>
			<tr>
				<th>ID</th>
				<th>IP</th>
				<th>Sensor 1</th>
				<th>Sensor 2</th>
				<th>Sensor 3</th>
				<th>CPU</th>
				<th>Date</th>
			</tr>
		</thead>
	</table>
	<!-- Configuration for the server side table -->
	<script>
		$(document).ready(function() {
			var table = $('#example-table').DataTable({
				'searching': true,
				'lengthChange': true,
				'serverSide': true,
				'iDisplayLength': 200,
				'order': [[1, 'desc'], [2, 'asc']],
				'ajax': '/example_datatables',
				'lengthMenu': [10, 25, 50, 100, 150, 200, 250, 300, 400, 500],
			});
			// Reload table every 30 seconds
			setInterval(function() {
				table.ajax.reload(function() {}, false);
			}, 30000);
		});
	</script>
</body>
<html>
```

Your **main.css** to include needed styling and things such as the icons for the column sorting:

```
.sorting {
	background: url("sort_both.png") no-repeat center right !important;
}
.sorting_desc {
	background: url("sort_desc.png") no-repeat center right !important;
}
.sorting_asc {
	background: url("sort_asc.png") no-repeat center right !important;
}
thead > tr > th {
	text-align: center;
}
```

Your **main Flask app** would be something like this:

```
import re
from datetime import datetime

import flask

# Here you'd import the DataTables plugin
from datatables import DataTablesServer

app = Flask(__name__)


# Utility function for parsing booleans from the DataTables requests
def parse_bool(value):
	if value.isdigit():
		if int(value) == 0:
			return False
		else:
			return True

	elif value.lower() == "true":
		return True

	elif value.lower() == "false":
		return False


@app.route('/example', methods = ['GET'])
def example():
	return flask.render_template('index.html')


# Method the DataTables client plugin will call
@app.route('/example_datatables', methods = ['GET'])
def example_datatables():
	# Set the name for the column, and it's mapping on the database
	columns = [
		('ID', ['id']),
		('IP', ['ip']),
		('Sensor 1', ['sensors', 0, 'reading']),
		('Sensor 2', ['sensors', 1, 'reading']),
		('Sensor 3', ['sensors', 2, 'reading']),
		('CPU', 'temp_cpu'),
		('Date', 'date')
	]

	# Columns you want to be able to search from, let's assume we want to
	# search by device ID and IP in here. It's an array of dictionaries.
	# Each dictionary will map to the columns, so column 0 will be
	# the first index element from the columns data. In case the search
	# column is a string, you might want to enable the ignorecase and
	# substring options so it ignores case when searching, and so that
	# you can find partial matches with the substring option.
	filter_columns = [
		{
			'column': 0,
			'ignorecase': True,
			'substring': True
		},
		{
			'column': 1,
			'ignorecase': False,
			'substring': False
		}
	]


	# Columns to sort from, 1 is ascendant, -1 is descendant. Or use
	# DataTablesServer.ASC or DataTablesServer.DESC instead
	example_index = [
		(0, DataTablesServer.DESC)
	]


	# You can use a custom filtering function so that you can manage
	# even further how filtering will work. You can take a look at the
	# default function from the class, to get an idea of how this works
	def custom_filtering_function(request_values, columns, filter_columns):
		filtering_data = {}

		for index, column in enumerate(columns):
			# Check if the column is searchable both client side and
			# server side
			valid_search_columns = [x['column'] for x in filter_columns]

			searchable = parse_bool(request_values['columns[{}][searchable]'.format(index)])
			search_value = request_values['columns[{}][search][value]'.format(index)]

			if searchable is True and search_value != "" and index in valid_search_columns:
				# From the corresponding column, get its mapping, an
				# example might be sensors.0.reading
				search_in = '.'.join(str(x) for x in column[1])

				# Save the mapping along the options for the filtering
				# of that column
				filtering_data[search_in] = {
					'$regex': re.compile(
						re.escape(search_value),
						re.IGNORECASE
					)
				}


		if not filtering_data:
			return None

		return filtering_data



	# Initialize the table object here, and give it the starting data.
	# request needs to be the Flask request object
	# columns will be the columns variable you defined
	# index will be the columns to sort by default (however, any sorting
	# request coming from the client has priority).
	# custom_filtering_function, mongo_host and mongo_port have default
	# values (the ones posted here are the default ones).
	table = DataTablesServer(
		request = request,
		columns = columns,
		index = None,
		filter_columns = filter_columns,
		db_name = 'Example',
		collection = 'sensors',
		custom_filtering_function = None,
		mongo_host = 'localhost',
		mongo_port = 27017
	)



	# After you set the data, you only need to call the output_result
	# function to make it work. It takes two parameters that allow you
	# to control the return values certain columns will return. An example
	# of such a function would be this one
	def custom_return_data(column, column_index, record):
		# Imagine we might want to display the date field a certain way.
		# In this case I'll use the European format as an example. By
		# default the plugin will just return the element as it appears
		if column_index == 6:
			return record['date'].strftime('%d-%m-%Y %H:%M:%S')


	return flask.jsonify(table.output_result(
		process_data_columns = [6],
		process_data_function = custom_return_data
	))
```
