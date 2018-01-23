# Server side DataTables plugin for a Flask and MongoDB application with no ORM

I needed to implement a very basic table with data that would be reported in constantly from multiple devices within Spain, and I decided to go with Flask and MongoDB (both because they wanted something quick, and because I felt like learning those two would allow me to easily add more stuff on top further down the road).

Issue was, I couldn't find any server side plugins for this combination, only one for when you use an ORM, which I wanted to avoid. The best I could find [was a very old class](https://gist.github.com/illerucis/4586359) (in which this is based) that used to work with early versions of DataTables, but not the most recent one.

So I decided to modify it and make it work with the newer versions so I could have a somewhat general solution that I could use in other projects as well.


## How to use

First you need to have both [Flask](http://flask.pocoo.org/docs/latest/) and [pymongo](https://api.mongodb.com/python/current/) installed in either your Python path or your virtual environment, whichever you're going to use.

Then you need your Flask application. Let's assume this is your application file hierarchy:

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

Your index.html file would have a simple table such as:

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
	<table id="example-table"></table>
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

Your main.css to include needed styling and things such as the icons for the column sorting:

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
