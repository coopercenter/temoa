from temoa_lib import TemoaError
from os.path import abspath, isfile

def db_2_dat(ifile, ofile):
	# Adapted from DB_to_DAT.py
	import sqlite3
	import sys
	import re
	import getopt

	def query_table (t_properties, f):
	    t_type = t_properties[0]  #table type (set or param)
	    t_name = t_properties[1]  #table name
	    t_flag = t_properties[3]  #table flag, if any
	    t_index = t_properties[4] #table column index after which '#' should be specified
	    if type(t_flag) is list:  #tech production table has a list for flags; this is currently hard-wired
		db_query = "SELECT * FROM " + t_name + " WHERE flag=='p' OR flag=='pb' OR flag=='ps'"
		dat_table_name = t_properties[2]
		if t_type == "set":
		    f.write("set " + dat_table_name + " := \n")
		else:
		    f.write("param " + dat_table_name + " := \n")
	    elif t_flag != '':    #check to see if flag is empty, if not use it to make table
		db_query = "SELECT * FROM " + t_name + " WHERE flag=='" + t_flag + "'"
		dat_table_name = t_properties[2]
		if t_type == "set":
		    f.write("set " + dat_table_name + " := \n")
		else:
		    f.write("param " + dat_table_name + " := \n")
	    else:    #Only other possible case is no flag
		db_query = "SELECT * FROM " + t_name
		if t_type == "set":
		    f.write("set " + t_name + " := \n")
		else:
		    f.write("param " + t_name + " := \n")
	    cur.execute(db_query)
	    if t_index == 0:    #make sure that units and descriptions are commented out in DAT file
		for line in cur:
		    str_row = str(line[0]) + "\n"
		    f.write(str_row)
		    print str_row
	    else:
		for line in cur:
		    before_comments = line[:t_index+1]    
		    before_comments = re.sub('[(]', '', str(before_comments))
		    before_comments = re.sub('[\',)]', '    ', str(before_comments))
		    after_comments = line[t_index+2:]
		    after_comments = re.sub('[(]', '', str(after_comments))
		    after_comments = re.sub('[\',)]', '    ', str(after_comments)) 
		    search_afcom = re.search(r'^\W+$', str(after_comments))		#Search if after_comments is empty.
		    if not search_afcom :
		    	str_row = before_comments + "# " + after_comments + "\n"
		    else :
					str_row = before_comments + "\n"
		    f.write(str_row)
		    print str_row                
	    f.write(';\n\n')

	#[set or param, table_name, DAT fieldname, flag (if any), index (where to insert '#')
	table_list =[['set','time_periods','time_exist','e',0], \
		     ['set','time_periods','time_future','f',0], \
		     ['set','time_season','','',0],    \
		     ['set','time_of_day','','',0],    \
		     ['set','technologies','tech_resource','r',0],  \
		     ['set','technologies','tech_production',['p','pb','ps'],0], \
		     ['set','technologies','tech_baseload','pb',0], \
		     ['set','technologies','tech_storage','ps',0],  \
		     ['set','commodities','commodity_physical','p',0],   \
		     ['set','commodities','commodity_emissions','e',0],   \
		     ['set','commodities','commodity_demand','d',0],   \
		     ['param','SegFrac','','',2],        \
		     ['param','DemandSpecificDistribution','','',3],  \
		     ['param','CapacityToActivity','','',1],          \
		     ['param','GlobalDiscountRate','','',0],          \
		     ['param','EmissionActivity','','',5],            \
		     ['param','Demand','','',2],                      \
		     ['param','TechOutputSplit','','',2],             \
		     ['param','MinCapacity','','',2],                 \
		     ['param','MaxCapacity','','',2],                 \
		     ['param','LifetimeTech','','',1],                \
		     ['param','LifetimeProcess','','',2],             \
		     ['param','LifetimeLoanTech','','',1],            \
		     ['param','CapacityFactorTech','','',3],          \
		     ['param','CapacityFactorProcess','','',4],       \
		     ['param','Efficiency','','',4],                  \
		     ['param','ExistingCapacity','','',2],            \
		     ['param','CostInvest','','',2],                  \
		     ['param','CostFixed','','',3],                   \
		     ['param','CostVariable','','',3]]


	#create a file to write output
	f = open(ofile, 'w')
	f.write('data ;\n\n')
	#connect to the database
	con = sqlite3.connect(ifile)
	cur = con.cursor()   # a database cursor is a control structure that enables traversal over the records in a database
	con.text_factory = str #this ensures data is explored with the correct UTF-8 encoding

	for table in table_list:
	    query_table(table, f)


	f.close()   
	cur.close()
	con.close()

class TemoaConfigError ( TemoaError ): pass

class TemoaConfig( object ):
	states = (
	('mga', 'exclusive'),
	)
	
	tokens = (
		'dot_dat',
		'output',
		'scenario',
		'fix_variables',
		'how_to_cite',
		'version',
		'solver',
		'generate_solver_lp_file',
		'keep_pyomo_lp_file',
		'eciu',
		'saveEXCEL',
		'mgaslack',
		'mgaiter'
	)
	
	t_ANY_ignore  = '[ \t]'
	
	def __init__(self, **kwargs):
		from Queue import Queue
		
		self.__error          = list()
		self.__mga_todo       = Queue()
		self.__mga_done       = Queue()
		
		self.file_location    = None
		self.dot_dat          = list() # Use Kevin's name.
		self.output           = None # May update to a list if multiple output is required.
		self.scenario         = None
		self.saveEXCEL        = False
		self.how_to_cite      = None
		self.version          = False
		self.fix_variables    = None
		self.generateSolverLP = False
		self.keepPyomoLP      = False
		self.eciu             = None
		self.mga              = None # mga slack value
		self.mga_iter         = None

		# To keep consistent with Kevin's argumetn parser, will be removed in the futre.
		self.graph_format     = None
		self.show_capacity    = False
		self.graph_type       = 'separate_vintages'
		self.use_splines      = False
		
		if 'd_solver' in kwargs.keys(): 
			self.solver = kwargs['d_solver']
		else:
			self.solver = None

	def __repr__(self): 
		width = 25
		spacer = '\n' + '-'*width + '\n'
		msg = spacer
		msg += '{:>{}s}: {}\n'.format('Config file', width, self.file_location)
		for i in self.dot_dat:
			if self.dot_dat.index(i) == 0:
				msg += '{:>{}s}: {}\n'.format('Input file', width, i)
			else:
				msg += '{:>25s}  {}\n'.format(' ', i)
		msg += '{:>{}s}: {}\n'.format('Output file', width, self.output)
		msg += '{:>{}s}: {}\n'.format('Scenario', width, self.scenario)	
		msg += '{:>{}s}: {}\n'.format('Spreadsheet output', width, self.saveEXCEL)
		msg += spacer
		msg += '{:>{}s}: {}\n'.format('Citation output status', width, self.how_to_cite)
		msg += '{:>{}s}: {}\n'.format('Version output status', width, self.version)
		msg += '{:>{}s}: {}\n'.format('Fixed variable file', width, self.fix_variables)
		msg += spacer
		msg += '{:>{}s}: {}\n'.format('Selected solver status', width, self.solver)
		msg += '{:>{}s}: {}\n'.format('Solver LP write status', width, self.generateSolverLP)
		msg += '{:>{}s}: {}\n'.format('Pyomo LP write status', width, self.keepPyomoLP)
		msg += spacer
		msg += '{:>{}s}: {}\n'.format('MGA slack value', width, self.mga)
		msg += '{:>{}s}: {}\n'.format('MGA # of iterations', width, self.mga_iter)
		msg += spacer
		msg += '{:>{}s}: {}\n'.format('Stochastic eciu', width, self.eciu)
		return msg

	def t_ANY_COMMENT(self, t):
		r'\#.*'
		pass
	
	def t_dot_dat(self, t):
		r'--input(\s+|\=)[-\\\/\:\.\~\w]+\.dat\b|--input(\s+|\=)[-\\\/\:\.\~\w]+\.db\b'
		self.dot_dat.append(abspath(t.value.replace('=', ' ').split()[1]))
	
	def t_output(self, t):
		r'--output(\s+|\=)[-\\\/\:\.\~\w]+\.db\b'
		self.output = abspath(t.value.replace('=', ' ').split()[1])
	
	def t_scenario(self, t):
		r'--scenario(\s+|\=)\w+\b'
		self.scenario = t.value.replace('=', ' ').split()[1]
	
	def t_saveEXCEL(self, t):
		r'--saveEXCEL\b'
		self.saveEXCEL = True
	
	def t_how_to_cite(self, t):
		r'--how_to_cite\b'
		self.how_to_cite = True

	def t_version(self, t):
		r'--version\b'
		self.version = True

	def t_fix_variables(self, t):
		r'--fix_variables(\s+|\=)[-\\\/\:\.\~\w]+\b'
		self.fix_variables = abspath(t.value.replace('=', ' ').split()[1])

	def t_solver(self, t):
		r'--solver(\s+|\=)\w+\b'
		self.solver = t.value.replace('=', ' ').split()[1]
	
	def t_generate_solver_lp_file(self, t):
		r'--generate_solver_lp_file\b'
		self.generateSolverLP = True
	
	def t_keep_pyomo_lp_file(self, t):
		r'--keep_pyomo_lp_file\b'
		self.keepPyomoLP = True
		
	def t_eciu(self, t):
		r'--eciu(\s+|\=)[-\\\/\:\.\~\w]+\b'
		self.eciu = abspath(t.value.replace('=', ' ').split()[1])
    
	def t_begin_mga(self, t):
		r'--mga(\s)*\{'
		t.lexer.push_state('mga')
		t.lexer.level = 1
	
	def t_mga_mgaslack(self, t):
		r'slack(\s+|\=)[\.\d]+'
		self.mga = float(t.value.replace('=', ' ').split()[1])
		
	def t_mga_mgaiter(self, t):
		r'iteration(\s+|\=)[\d]+'
		self.mga_iter = int(t.value.replace('=', ' ').split()[1])
		
	def t_mga_end(self, t):
		r'\}'
		t.lexer.pop_state()
		t.lexer.level -= 1
	
	def t_ANY_newline(self,t):
		r'\n+|(\r\n)+|\r+' # '\n' (In linux) = '\r\n' (In Windows) = '\r' (In Mac OS)
		t.lexer.lineno += len(t.value)
	
	def t_ANY_error(self, t):
		if not self.__error:
			self.__error.append({'line': [t.lineno, t.lineno], 'index': [t.lexpos, t.lexpos], 'value': t.value[0]})
		elif t.lexpos - self.__error[-1]['index'][-1] == 1:
			self.__error[-1]['line' ][-1] = t.lineno
			self.__error[-1]['index'][-1] = t.lexpos
			self.__error[-1]['value'] += t.value[0]
		else:
			self.__error.append({'line': [t.lineno, t.lineno], 'index': [t.lexpos, t.lexpos], 'value': t.value[0]})
		t.lexer.skip(1)

	def next_mga(self):
		if not self.__mga_todo.empty():
			self.__mga_done.put(self.scenario)
			self.scenario = self.__mga_todo.get()
			return True
		else:
			return False
	
	def build(self,**kwargs):
		import ply.lex as lex, os, sys
		if 'config' in kwargs:
			if isfile(kwargs['config']):
				self.file_location= abspath(kwargs.pop('config'))
			else:
				msg = 'No such file exist: {}'.format(kwargs.pop('config'))
				raise TemoaConfigError( msg )

		self.lexer = lex.lex(module=self, **kwargs)
		if self.file_location:
			with open(self.file_location, 'rb') as f:
				self.lexer.input(f.read())
			while True:
				tok = self.lexer.token()
				if not tok: break
		
		if self.__error:
			msg = '\nIllegal character(s) in config file:\n'
			msg += '-'*25 + '\n'
			for e in self.__error:
				msg += "Line {} to {}: '{}'\n".format(e['line'][0], e['line'][1], e['value'])
			msg += '-'*25 + '\n'
			sys.stderr.write(msg)
		
		if not self.dot_dat:
			raise TemoaConfigError('Input file not specified.')
		
		for i in self.dot_dat:
			if not isfile(i):
				raise TemoaConfigError('Cannot locate input file: {}'.format(i))
		
		if not self.output:
			raise TemoaConfigError('Output file not specified.')
		
		if not isfile(self.output):
			raise TemoaConfigError('Cannot locate output file: {}.'.format(self.output))
		
		if not self.scenario:
			raise TemoaConfigError('Scenario name not specified.')
		
		if self.mga_iter:
			for i in range(self.mga_iter):
				self.__mga_todo.put(self.scenario + '_mga_' + str(i))

		f = open(os.devnull, 'w'); sys.stdout = f # Suppress the original DB_to_DAT.py output
		counter = 0
		for ifile in self.dot_dat:
			if ifile[-3:] == '.db':
				ofile = ifile[:-3] + '.dat'
				db_2_dat(ifile, ofile)
				self.dot_dat[self.dot_dat.index(ifile)] = ofile
				counter += 1
		f.close()
		sys.stdout = sys.__stdout__
		if counter > 0:
			sys.stderr.write("\n{} .db file(s) converted\n".format(counter))