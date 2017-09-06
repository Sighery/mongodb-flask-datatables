import json
import re

from pymongo import MongoClient
from flask import request


class DataTablesServer(object):
	def __init__(self, request, columns, index, filter_columns, db_name, collection, custom_filtering_function = None, mongo_host = 'localhost', mongo_port = 27017):
		# Dict with all the arguments from DataTables
		self.request_values = request.args

		# Columns to display and their representation in the DB, mapping example:
		# List of tupples in the order to be shown. First parameter column name
		# second paramenter mapping to the collection
		#[
		#   (
		#       "Sensor 1": ['sondas', 0, 'temperatura']
		#   ),
		#   . . .
		#]
		self.columns = columns

		# Columns to sort from, example:
		#[
		#	(
		#   	0, 1
		#	),
		#	(
		#		2, -1
		#	)
		#]
		# 1 for ascendent, -1 for descendent
		self.index = index

		# List of dictionaries with the following syntax:
		# [
		#   {
		#       column: int,
		#       ignorecase: bool,
		#       substring: bool
		#   }
		# ]
		# The general search will work on the columns you pass here
		# substring set as True will allow for matches that contain given string
		# And ignorecase set as True will allow to match ignoring case
		self.filter_columns = filter_columns


		# Database to use
		self.db_name = db_name

		# Collection to pull results from
		self.collection = collection

		# Connection to MongoDB
		self.dbconn = MongoClient(mongo_host, mongo_port)

		# Results from the DB
		self.result_data = None

		# Rows in the table unfiltered
		self.rows_total = 0

		# Rows in the table filtered
		self.rows_filtered = 0

		# Translation for sorting between DataTables and MongoDB
		self.order_dict = {'asc': 1, 'desc': -1}

		# Custom function for how to deal with filtering
		self.custom_filtering_function = custom_filtering_function

		self.run_queries()


	def output_result(self, process_data_columns = None, process_data_function = None):
		'''
		Instead of the usual behaviour of accessing and displaying the data if
		you pass in process_data_columns, to tell it in which columns would you
		like to manually generate the data, and process_data_function to run
		a custom function, it will call that for each matched record and column,
		giving a better control of how is data generated and displayed.
		The process_data_function should be:

		def process_data(column, column_index, record):
			# Do something with the data in the record
			return cell_data
		'''

		output = {}
		output['draw'] = self.request_values['draw']
		output['recordsFiltered'] = self.rows_filtered
		output['recordsTotal'] = self.rows_total
		output['data'] = []

		for record in self.result_data:
			record_data = []

			for index, column in enumerate(self.columns):
				if process_data_function is not None and process_data_columns is not None and index in process_data_columns:
					# Custom func was provided, pass the data to it and append
					# to record_data the result of the custom function run
					record_data.append(process_data_function(column, index, record))

				else:
					column_data = self.access_item(record, column[1])

					record_data.append(column_data)


			# All columns matched, go ahead and append record_data to data
			output['data'].append(record_data)


		return output



	def _orderable_columns(self):
		'''
			Find all the columns that are orderable and their values (if any).
		'''

		data = {
			'orderables': [],
			'ordering': []
		}

		for index, column in enumerate(self.columns):
			try:
				idx_string = 'columns[{0}][orderable]'.format(index)

				if self._parse_bool(self.request_values[idx_string]) is True:
					data['orderables'].append(index)
			except:
				pass


		for elem in range(len(data['orderables'])):
			try:
				order_column = 'order[{0}][column]'.format(elem)
				order_dir = 'order[{0}][dir]'.format(elem)

				column_index = self.request_values[order_column]
				dir_value = self.request_values[order_dir]

				if column_index.isdigit() is False or dir_value not in self.order_dict:
					continue

				column_path = '.'.join(str(x) for x in self.columns[int(column_index)][1])
				column_order_dir = self.order_dict.get(dir_value)

				data['ordering'].append((column_path, column_order_dir))
			except KeyError:
				break


		return data



	def access_item(self, record, path):
		'''
			Usually private method, used within the class to access items and
		retrieve the result (or None in case the element didn't exist).

			It accepts two arguments:
			`record`: Represents each "row" from a DB call.
			`path`: Element to find within that record, following that path.

		Example record and path:
		record = {
			'id': 'TEST',
			'status': 0,
			'alarms': [
				{
					'id': 0,
					'status': False
				},
				{
					'id': 4,
					'status': True
				}
			]
		}

		path = ['alarms', 2, 'status']

			That would access the 'alarms' element, then as it is an array, it
		would try to access the second element in that array, and then fetch the
		'status' value. If any of those steps failed, it would simply return
		None.
		'''

		result = record

		for step in path:
			try:
				result = result[step]
			except IndexError:
				return None
			except KeyError:
				return None

		return result


	def run_queries(self):
		# Connection to your DB
		mydb = self.dbconn[self.db_name]

		# Start and length for pages
		pages = self.paging()

		# The term to search the DB in for if any
		if self.custom_filtering_function is not None:
			search_for = self.filtering(self.custom_filtering_function)
		else:
			search_for = self.filtering()

		# The sorting to sort for
		sorting = self.sorting()

		# Result from DB to display on the page
		self.result_data = mydb[self.collection].find(
			filter = search_for,
			limit = pages['length'],
			skip = pages['start'],
			sort = sorting
		)

		# Length of filtered set
		self.rows_filtered = mydb[self.collection].find(filter = search_for).count()

		# Length of all results unfiltered
		self.rows_total = mydb[self.collection].find().count()



	def paging(self):
		pages = {
			"start": 0,
			"length": 0
		}

		pages['start'] = int(self.request_values['start'])
		pages['length'] = int(self.request_values['length'])

		return pages


	def sorting(self):
		req_order = self._orderable_columns()

		if len(req_order['ordering']) > 0:
			return req_order['ordering']

		elif self.index is not None:
			order_data = []

			for order_values in self.index:
				order_column = '.'.join(str(x) for x in self.columns[order_values[0]][1])

				order_data.append((order_column, order_values[1]))

			return order_data

		elif self.index is None:
			return None



	def _parse_bool(self, bool_str):
		if bool_str.lower() == "true":
			return True
		elif bool_str.lower() == "false":
			return False



	def filtering(self, process_data_function = None):
		'''
		By default it tries to match every column with a value and searchable set
		as True in the DB, and every value passed to the general Search input of
		DataTables. If none of this is set, it returns None.

		It searches the general Search input on the column passed to filter_column.

		The matching is done by default using a regex (so allows substrings), and
		case insensitive.

		You can pass your own custom function to deal with the parsing like this:
		def process_data_function(request_values, columns, filter_column):
			# Do something
			return filter_dict
			# Or return None
		'''

		if process_data_function is not None:
			return process_data_function(self.request_values, self.columns, self.filter_columns)

		else:
			filtering_data = {}

			# Get all the columns that have searchable set as true, and that have any
			# search input, and add it to the result filtering dictionary
			for index, column in enumerate(self.columns):
				searchable = self._parse_bool(self.request_values['columns[' + str(index) + '][searchable]'])
				search_value = self.request_values['columns[' + str(index) + '][search][value]']

				if searchable is True and search_value != "":
					search_in = '.'.join(str(x) for x in column[1])

					filtering_data[search_in] = {
						'$regex': re.compile(
							re.escape(search_value),
							re.IGNORECASE
						)
					}



			# Filters on the columns you pass for filtering
			if self.filter_columns is not None and 'search[value]' in self.request_values \
			and self.request_values['search[value]'] is not "":
				# Figure out if this is a multi-column search
				multiple_filter_columns = None
				if len(self.filter_columns) > 1:
					filtering_data['$or'] = []
					multiple_filter_columns = True


				search_value = self.request_values['search[value]']

				for filter_column in self.filter_columns:
					search_in = '.'.join(str(x) for x in self.columns[filter_column['column']][1])

					if filter_column['ignorecase'] and filter_column['substring'] \
					and multiple_filter_columns is not None:
						filtering_data['$or'].append({
							search_in: {
								'$regex': re.compile(
									re.escape(search_value),
									re.IGNORECASE
								)
							}
						})

					elif filter_column['ignorecase'] and filter_column['substring'] \
					and multiple_filter_columns is None:
						filtering_data[search_in] = {
							'$regex': re.compile(
								re.escape(search_value),
								re.IGNORECASE
							)
						}

					elif filter_column['substring'] and multiple_filter_columns is not None:
						filtering_data['$or'].append({
							search_in: {
								'$regex': re.compile(
									re.escape(search_value)
								)
							}
						})


					elif filter_column['substring'] and multiple_filter_columns is None:
						filtering_data[search_in] = {
							'$regex': re.compile(
								re.escape(search_value)
							)
						}

					elif filter_column['ignorecase'] and multiple_filter_columns is not None:
						filtering_data['$or'].append({
							search_in: {
								'$regex': re.compile(
									re.escape("^" + search_value + "$"),
									re.IGNORECASE
								)
							}
						})

					elif filter_column['ignorecase'] and multiple_filter_columns is None:
						filtering_data[search_in] = {
							'$regex': re.compile(
								re.escape("^" + search_value + "$"),
								re.IGNORECASE
							)
						}

					elif multiple_filter_columns is not None:
						filtering_data['$or'].append({
							search_in: search_value
						})

					elif multiple_filter_columns is None:
						filtering_data[search_in] = search_value


			# Finally find out if there were any filters passed, if so pass filtered_data
			# if not just return None
			if not filtering_data:
				return None
			else:
				return filtering_data
