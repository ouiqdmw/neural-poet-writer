import codecs
import numpy as np
from utils.code_book import code_book
from utils.data_cutter import data_cutter

class data_gatherer():
	def __init__(self, rawfile_dir, midfile_dir, encoding='utf-8'):
		self.poem_set = 'poem_set.txt'
		self.title_set = 'title_set.txt'
		self.encoding = encoding

		self.rawfile_dir = rawfile_dir
		self.midfile_dir = midfile_dir
		self.cutter = data_cutter('control_data')

	def path_parse(self, text):
		title = list()
		data = list()
		start = text.find('POEM_TITLE\n')
		while(start != -1):
			text = text[start+len('POEM_TITLE\n'):]
			middle = text.find('POEM_DATA\n')
			start = text.find('POEM_TITLE\n')
			
			title_text = text[:middle-1]
			title_text = self.cutter.data_cut(title_text)
			title.append(title_text)
			if(start == -1):
				data_text = text[middle+len('POEM_DATA\n'):-1]
				data_text = self.cutter.data_cut(data_text)
				data.append(data_text)
			else:
				data_text = text[middle+len('POEM_DATA\n'):start-1]
				data_text = self.cutter.data_cut(data_text)
				data.append(data_text)
		return title, data
	def clean(self):
		f = codecs.open(self.midfile_dir +'/'+ self.poem_set, "w", self.encoding)
		f.close()
		f = codecs.open(self.midfile_dir +'/'+ self.title_set, "w", self.encoding)
		f.close()
	def gather(self, path_list):
		f1 = codecs.open(self.midfile_dir +'/'+ self.poem_set, "a", self.encoding)
		f3 = codecs.open(self.midfile_dir +'/'+ self.title_set, "a", self.encoding)
		for path in path_list:
			with codecs.open(self.rawfile_dir +'/'+ path, "r", encoding=self.encoding) as f2:
				text = f2.read()
				# do text processing
				titles, data = self.path_parse(text)
				for i in range(len(data)):
					datum = data[i]
					title = titles[i]
					title_pos = len(datum)
					if(datum[-1]!='\n'):
						datum += '\n'
						title_pos += 1
					f1.write(datum)
					f3.write(title+'\n'+str(title_pos)+'\n')
			f2.close()
		f1.close()
		f3.close()

# drop/add
# normal/stride
# whole/one -------------------------------------> TODO

class batch_maker():
	def __init__(self, rawfile_dir, midfile_dir, batch_size=20, seq_len=20, stride=2, text_mode='add', seqs_mode='normal', batch_mode='whole', title_seq_save=False, encoding='utf-8'):
		self.stride = stride
		self.seq_len = seq_len
		self.batch_size = batch_size
		self.text_mode = text_mode
		self.seqs_mode = seqs_mode
		self.batch_mode = batch_mode
		self.title_seq_save = False
		self.encoding = encoding

		self.rawfile_dir = rawfile_dir
		self.midfile_dir = midfile_dir
	# drop leftover based on sequence length
	def dropped_text(self, text):
		seq_len = self.seq_len

		text_len = len(text)
		leftover = text_len % seq_len
		text_len = len(text)
		if(leftover != 0):
			text = text[:text_len - leftover]
		return text
	# pad not filled area based on sequence length, using front of text
	def added_text(self, text):
		seq_len = self.seq_len

		text_len = len(text)
		leftover = text_len % seq_len
		add_count = seq_len - leftover
		if(add_count != 0):
			text = text + text[:add_count]
		return text
	# return strided text area based on sequence length, if limit reached, return None	
	def seqs_stride_get(self, text, stride_idx, text_len):
		seq_len = self.seq_len

		if(text_len >= stride_idx + seq_len):
			return text[stride_idx:stride_idx + seq_len]
		else:
			return None

	# make sequences from source
	def seqs_normal(self, source, start, end, title_seq_save=False, title=''):
		seq_len = self.seq_len
		text_mode = self.text_mode

		text = source[start:end]
		prd = list()
		if(len(text) < seq_len):
			# 1 append routine
			text = self.added_text(text)
			prd.append(text)
		else:
			# 2 drop/append routine
			if(text_mode == 'add'):
				text = self.added_text(text)
			else:
				text = self.dropped_text(text)
			# split by seq_len
			prd.extend(text[0+idx:seq_len+idx] for idx in range(0, len(text), seq_len))
		# save title:seq_count data file
		if(title_seq_save):
			f = codecs.open(self.midfile_dir +'/'+ 'title_seqs.txt', "a", self.encoding)
			f.write(title+'\n'+str(len(prd))+'\n')
			f.close()
		return prd
	# make sequences from source, strided method
	def seqs_stride(self, source, start, end, title_seq_save=False, title=''):
		seq_len = self.seq_len

		text = source[start:end]
		prd = list()
		if(len(text) < seq_len):
			# 1 append routine
			text = self.added_text(text)
			prd.append(text)
		else:
			text_len = len(text)
			stride_idx = 0
			seq = self.seqs_stride_get(text, stride_idx, text_len)
			while(seq != None):
				# add seq to prd
				prd.append(seq)
				# slide
				stride_idx += stride
				# move
				seq = self.seqs_stride_get(text, stride_idx, text_len)
		# save title:seq_count data file
		if(title_seq_save):
			f = codecs.open(self.midfile_dir +'/'+ 'title_seqs.txt', "a", self.encoding)
			f.write(title+'\n'+str(len(prd))+'\n')
			f.close()
		return prd

	def titles_load(self, filename):
		f = codecs.open(self.midfile_dir +'/'+ filename, "r", encoding=self.encoding)
		lines = f.readlines()
		idx = 0
		titles = list()
		t_indice = list()
		while(idx + 1 >= len(lines)):
			titles.append(lines[idx])
			t_indice.append(lines[idx+1])
			idx += 2
		f.close()
		return titles, t_indice
	def make_batchs(self, source, title_filename):
		seqs_mode = self.seqs_mode
		batch_mode = self.batch_mode
		batch_size = self.batch_size

		count = 0
		batchs = list()
		batch = list()
		# get all seqs by seqs_ function
		# if whole, just move to seqs_mode branch with all scope -> title_save is automatically false
		if(batch_mode == 'whole'):
			if(seqs_mode == 'normal'):
				seqs = self.seqs_normal(source, 0, len(source))
			else:
				seqs = self.seqs_stride(source, 0, len(source))
		# else LOOP title file
		# 	make seqs(src, start, end, self.title_seq_save) with seqs_mode
		else:
			titles, t_indice = self.titles_load(title_filename)
			idx = 0
			t_start = 0
			t_end = 0
			seqs = list()
			while(idx < len(titles)):
				t_start = t_end
				t_end += t_indice[idx]
				if(seqs_mode == 'normal'):
					seqs += self.seqs_normal(source, t_start, t_end, self.title_seq_save, titles[idx])
				else:
					seqs += self.seqs_stride(source, t_start, t_end, self.title_seq_save, titles[idx])
				idx += 1
		# for each seq in seqs
		for seq in seqs:
			if(count >= batch_size):
				count = 0
				batchs.append(batch)
				batch = list()
			batch.append(seq)
			count += 1
		if(count >= batch_size):
			batchs.append(batch)
		return batchs
	def save_batchs(self, filename, batchs):
		stride = self.stride
		seq_len = self.seq_len
		batch_size = self.batch_size
		text_mode = self.text_mode
		seqs_mode = self.seqs_mode
		batch_mode = self.batch_mode
		title_save = self.title_seq_save

		f.codecs.open(self.midfile_dir +'/'+ filename, "w", encoding=self.encoding)
		f.write(str(stride)+"\n")
		f.write(str(seq_len)+"\n")
		f.write(str(batch_size)+"\n")
		f.write(str(text_mode)+"\n")
		f.write(str(seqs_mode)+"\n")
		f.write(str(batch_mode)+"\n")
		f.write(str(title_save)+"\n")

		for batch in batchs:
			for seq in batch:
				f.write(seq)
		f.close()
	def load_batchs(self, filename):
		seq_len = self.seq_len
		batch_size = self.batch_size

		f.codecs.open(self.midfile_dir +'/'+ filename, "r", encoding=self.encoding)
		text = f.read()

		seqs = list()
		batchs = list()
		seqs.extend(text[0+idx:seq_len+idx] for idx in range(0, len(text), seq_len))
		batchs.extend(seqs[0+idx:batch_size+idx] for idx in range(0, len(text), batch_size))
		return batchs




# https://github.com/sherjilozair/char-rnn-tensorflow/blob/master/utils.py
# https://chunml.github.io/ChunML.github.io/project/Creating-Text-Generator-Using-Recurrent-Neural-Network/
class data_loader():
	def __init__(self, seq_len, batch_size, rawfile_dir, midfile_dir, encoding='utf-8'):
		self.poem_set = "poem_set.txt"
		self.title_set = "title_set.txt"
		self.code_set = "code_set.txt"
		self.batch_set = "batch_set.txt"
		self.npbatch_set = "np_batchs.npy"
		self.seq_len = seq_len
		self.batch_size = batch_size
		self.encoding = encoding
		self.rawfile_dir = rawfile_dir
		self.midfile_dir = midfile_dir

		self.cb = code_book(midfile_dir)
		self.bm = batch_maker(
			rawfile_dir,
			midfile_dir,
			batch_size=batch_size,
			seq_len=seq_len,
			stride=2,
			text_mode='add',
			seqs_mode='normal',
			batch_mode='whole',
			title_seq_save=False)

	def set_dir(self, rawfile_dir, midfile_dir):
		self.rawfile_dir = rawfile_dir
		self.midfile_dir = midfile_dir
	def file_preprocess(self, textfile_end = 2123, file_prefix = 'text', file_postfix='.txt'):
		path_list = [(file_prefix+str(i)+file_postfix) for i in range(1, textfile_end + 1)]
		# gather data
		print('gatherer start')
		gatherer = data_gatherer(self.rawfile_dir, self.midfile_dir)
		gatherer.clean()
		gatherer.gather(path_list)

		# open source
		print('source read')
		f = codecs.open(self.midfile_dir +'/'+ self.poem_set, "r", self.encoding)
		source = f.read()
		f.close()

		# make vector, save
		print('code_book setup start')
		cb = self.cb
		for ch in source:
			cb.gather(ch)
		cb.sort_codes()
		print('code_book length : '+str(cb.size()))
		cb.save_to(self.code_set)


		# make batches
		print('batch making start')
		bm = self.bm
		batchs = bm.make_batchs(source, self.title_set)

		#save_batchs(self.batch_set, batchs)
		
		# make number batchs
		print('number batch making start')
		cb = self.cb
		number_batchs = cb.get_number_batchs(batchs)
		np_batchs = np.array(number_batchs)
		self.np_batchs = np_batchs

		print('preprocess done.')
		return
	def text_preprocess(self, source):
		# make vector, save
		print('code_book setup start')
		cb = self.cb
		for ch in source:
			cb.gather(ch)
		cb.sort_codes()
		print('code_book length : '+str(cb.size()))
		cb.save_to(self.code_set)

		# make batches
		print('batch making start')
		bm = self.bm
		batchs = bm.make_batchs(source, self.title_set)
		
		# make number batchs
		print('number batch making start')
		cb = self.cb
		number_batchs = cb.get_number_batchs(batchs)
		np_batchs = np.array(number_batchs)
		self.np_batchs = np_batchs

		print('preprocess done.')
		return
	def save(self):
		self.cb.save_to(self.code_set)
		np.save(self.midfile_dir +'/'+ self.npbatch_set, self.np_batchs)
	def load(self):
		# load vector
		cb = self.cb
		cb.load_from(self.code_set)
		# load batches
		#batchs = bm.load_batchs(self.batch_set)
		# load np_batchs
		np_batchs = np.load(self.midfile_dir +'/'+ self.npbatch_set)
		self.np_batchs = np_batchs
		return
