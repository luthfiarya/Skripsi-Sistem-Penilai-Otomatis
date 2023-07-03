from flask import Flask, render_template, request, redirect, url_for
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import numpy as np
import pandas as pd
import json
import re


class Preprocessing:
    def cleansing(self, string):
        # Remove Punctuation (tanda baca)
        string = ' '.join(string.split())
        string = re.sub(r'[^a-zA-Z0-9 ]', '', string)

        # Remove karakter yang terdiri dari satu kata
        string = re.sub(r'\b\w\b', '', string)

        # Remove non-ASCII
        string = string.encode('ascii', 'ignore').decode('utf-8')
        string = re.sub(r'[^\x00-\x7f]', r'', string)
        return string

    def case_folding(self, string):
        string = str.lower(string)
        return string

    def filtering(self, string):
        factory = StopWordRemoverFactory()
        stopword = factory.create_stop_word_remover()
        string = stopword.remove(string)
        return string

    def whitespace_removal(self, string):
        string = string.replace(" ", "")
        return string

    def preprocessing(self, string):
        processed_string = self.cleansing(string)
        processed_string = self.case_folding(processed_string)
        processed_string = self.filtering(processed_string)
        return processed_string


class AlgoritmaRO:
    def frontMaxMatch(self, s1, s2):
        longest = 0
        longestsubstring = ""
        for i in range(0, len(s1), 1):
            for j in range(i+1, len(s1)+1, 1):
                substring = s1[i:j]
                if substring in s2 and len(substring) > longest:
                    longest = len(substring)
                    longestsubstring = substring
        return longestsubstring

    def getMatchList(self, s1, s2):
        list = []
        match = self.frontMaxMatch(s1, s2)

        if len(match) > 0:
            frontsource = s1[0:s1.find(match)]
            fronttarget = s2[0:s2.find(match)]
            # Get Longest Substring From Left of Anchor
            frontqueue = self.getMatchList(frontsource, fronttarget)
            endsource = s1[s1.find(match) + len(match):]
            endtarget = s2[s2.find(match) + len(match):]
            # Get Longest Substring Right of Anchor
            endqueue = self.getMatchList(endsource, endtarget)
            list.append(match)
            list.extend(frontqueue)
            list.extend(endqueue)

        return list

    def algoritma_ro(self, s1, s2):
        if len(s1) == 0 and len(s2) == 0:
            return

        match = self.getMatchList(s1, s2)
        km = 0

        for match_partial in match:
            km += len(match_partial)
            print(match_partial)

        print(km)
        print(len(s1)+len(s2))
        return round((2 * km) / (len(s1) + len(s2)) * 100, 2)


class SynonymRecognition:
    def __init__(self):
        f = open('D:/Coding Skripsi/Kamus Sinonim/dict.json')
        synonym_json = json.load(f)
        self.entries = {}

        for key in synonym_json:
            self.insert(key.strip())
            for synonym_word in synonym_json[key]["sinonim"]:
                self.register_synonym(key.strip(), synonym_word.strip())

    def insert(self, word):
        if not self.has_entry(word):
            self.entries[word] = {
                "word": word,
                "synonyms": []
            }

    def register_synonym(self, key, word):
        self.insert(key)
        self.insert(word)
        self.entries[key]["synonyms"].append(word)
        self.entries[word]["synonyms"].append(key)

    def has_entry(self, word):
        return word in self.entries

    def are_synonyms(self, key, word):
        if self.has_entry(key) and self.has_entry(word):
            return word in self.entries[key]["synonyms"] or key in self.entries[word]["synonyms"]
        return False

    def get_synonyms(self, word):
        if self.has_entry(word):
            return self.entries[word]["synonyms"]
        else:
            return []

    def synonym_recognition(self, jawaban, kunci):
        list_kunci = kunci.split()
        list_jawaban = jawaban.split()
        for i in range(len(list_jawaban)):
            for kata in list_kunci:
                if kata == list_jawaban[i]:
                    list_kunci.remove(kata)
                    break
                if self.are_synonyms(list_jawaban[i], kata):
                    list_jawaban[i] = kata
                    list_kunci.remove(kata)
                    break

        return " ".join(list_jawaban)


class Processing:
    def __init__(self):
        self.preprocess = Preprocessing()
        self.synonym = SynonymRecognition()
        self.algoritma = AlgoritmaRO()

    def processing_dengan_synonym(self, string_1, string_2):
        kunci_jawaban_preprocessing = self.preprocess.preprocessing(string_2)
        kunci_jawaban_processing = self.preprocess.whitespace_removal(
            kunci_jawaban_preprocessing)

        jawaban_preprocessing = self.preprocess.preprocessing(string_1)
        jawaban_synonym = self.synonym.synonym_recognition(
            jawaban_preprocessing, kunci_jawaban_preprocessing)
        jawaban_processing = self.preprocess.whitespace_removal(
            jawaban_synonym)

        hasil_algoritma = self.algoritma.algoritma_ro(
            jawaban_processing, kunci_jawaban_processing)
        return hasil_algoritma

    def processing_tanpa_synonym(self, string_1, string_2):
        kunci_jawaban_preprocessing = self.preprocess.preprocessing(string_2)
        kunci_jawaban_processing = self.preprocess.whitespace_removal(
            kunci_jawaban_preprocessing)

        jawaban_preprocessing = self.preprocess.preprocessing(string_1)
        jawaban_processing = self.preprocess.whitespace_removal(
            jawaban_preprocessing)

        hasil_algoritma = self.algoritma.algoritma_ro(
            jawaban_processing, kunci_jawaban_processing)
        return hasil_algoritma


class PengujianPreprocessingFile:
    def __init__(self):
        self.preprocessing = Preprocessing()
        self.synonym = SynonymRecognition()
        self.df_jawaban = pd.read_csv('jawaban.csv')
        self.df_kunci = pd.read_csv('kunci_jawaban.csv')

    def preprocessing_kunci_jawaban(self):
        self.df_kunci_jawaban_hasil_preprocessing = pd.DataFrame(columns=[])
        self.df_kunci_jawaban_hasil_preprocessing['kunci_jawaban'] = self.df_kunci['kunci_jawaban']
        self.df_kunci_jawaban_hasil_preprocessing['hasil_cleansing'] = self.df_kunci_jawaban_hasil_preprocessing['kunci_jawaban'].apply(
            lambda x: self.preprocessing.cleansing(x))
        self.df_kunci_jawaban_hasil_preprocessing['hasil_case_folding'] = self.df_kunci_jawaban_hasil_preprocessing['hasil_cleansing'].apply(
            lambda x: self.preprocessing.case_folding(x))
        self.df_kunci_jawaban_hasil_preprocessing['hasil_filtering'] = self.df_kunci_jawaban_hasil_preprocessing['hasil_case_folding'].apply(
            lambda x: self.preprocessing.filtering(x))
        self.df_kunci_jawaban_hasil_preprocessing['hasil_whitespace_removal'] = self.df_kunci_jawaban_hasil_preprocessing['hasil_filtering'].apply(
            lambda x: self.preprocessing.whitespace_removal(x))

        return self.df_kunci_jawaban_hasil_preprocessing

        # self.df_kunci_jawaban_hasil_preprocessing.to_excel(
        #     'D:\Coding Skripsi\Hasil Preprocessing\hasil_preprocessing_kunci_jawaban.xlsx')

    def preprocessing_jawaban(self, jawaban, indeks):
        self.df_jawaban_hasil_preprocessing = pd.DataFrame(columns=[])
        self.df_jawaban_hasil_preprocessing['siswa'] = self.df_jawaban['siswa']
        self.df_jawaban_hasil_preprocessing['jawaban'] = self.df_jawaban[jawaban]
        self.df_jawaban_hasil_preprocessing['hasil_cleansing'] = self.df_jawaban_hasil_preprocessing['jawaban'].apply(
            lambda x: self.preprocessing.cleansing(x))
        self.df_jawaban_hasil_preprocessing['hasil_case_folding'] = self.df_jawaban_hasil_preprocessing['hasil_cleansing'].apply(
            lambda x: self.preprocessing.case_folding(x))
        self.df_jawaban_hasil_preprocessing['hasil_filtering'] = self.df_jawaban_hasil_preprocessing['hasil_case_folding'].apply(
            lambda x: self.preprocessing.filtering(x))

        kj = self.df_kunci['kunci_jawaban'][indeks]
        kj = self.preprocessing.preprocessing(kj)

        self.df_jawaban_hasil_preprocessing['hasil_synonym_recognition'] = self.df_jawaban_hasil_preprocessing['hasil_filtering'].apply(
            lambda x: self.synonym.synonym_recognition(x, kj))
        self.df_jawaban_hasil_preprocessing['hasil_whitespace_removal'] = self.df_jawaban_hasil_preprocessing['hasil_synonym_recognition'].apply(
            lambda x: self.preprocessing.whitespace_removal(x))
        file_name = f'hasil_preprocessing_jawaban_{indeks+1}.xlsx'
        self.df_jawaban_hasil_preprocessing.to_excel(
            'D:/Coding Skripsi/Hasil Preprocessing/' + file_name)

    def loop_preprocessing_jawaban(self):
        for i in range(10):
            self.preprocessing_jawaban(f'jawaban_{i+1}', i)


class PengujianAlgoritmaFile:
    def __init__(self):
        self.processing = Processing()
        self.df_jawaban = pd.read_csv('jawaban.csv')
        self.df_kunci = pd.read_csv('kunci_jawaban.csv')
        self.kj_1 = self.df_kunci['kunci_jawaban'][0]
        self.kj_2 = self.df_kunci['kunci_jawaban'][1]
        self.kj_3 = self.df_kunci['kunci_jawaban'][2]
        self.kj_4 = self.df_kunci['kunci_jawaban'][3]
        self.kj_5 = self.df_kunci['kunci_jawaban'][4]
        self.kj_6 = self.df_kunci['kunci_jawaban'][5]
        self.kj_7 = self.df_kunci['kunci_jawaban'][6]
        self.kj_8 = self.df_kunci['kunci_jawaban'][7]
        self.kj_9 = self.df_kunci['kunci_jawaban'][8]
        self.kj_10 = self.df_kunci['kunci_jawaban'][9]

    def ro_dengan_synonym(self):
        self.df_hasil_dengan_synonym = pd.DataFrame(columns=[])
        self.df_hasil_dengan_synonym['siswa'] = self.df_jawaban['siswa']
        self.df_hasil_dengan_synonym['hasil_ro_1'] = self.df_jawaban['jawaban_1'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_1))
        self.df_hasil_dengan_synonym['hasil_ro_2'] = self.df_jawaban['jawaban_2'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_2))
        self.df_hasil_dengan_synonym['hasil_ro_3'] = self.df_jawaban['jawaban_3'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_3))
        self.df_hasil_dengan_synonym['hasil_ro_4'] = self.df_jawaban['jawaban_4'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_4))
        self.df_hasil_dengan_synonym['hasil_ro_5'] = self.df_jawaban['jawaban_5'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_5))
        self.df_hasil_dengan_synonym['hasil_ro_6'] = self.df_jawaban['jawaban_6'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_6))
        self.df_hasil_dengan_synonym['hasil_ro_7'] = self.df_jawaban['jawaban_7'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_7))
        self.df_hasil_dengan_synonym['hasil_ro_8'] = self.df_jawaban['jawaban_8'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_8))
        self.df_hasil_dengan_synonym['hasil_ro_9'] = self.df_jawaban['jawaban_9'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_9))
        self.df_hasil_dengan_synonym['hasil_ro_10'] = self.df_jawaban['jawaban_10'].apply(
            lambda x: self.processing.processing_dengan_synonym(x, self.kj_10))
        self.df_hasil_dengan_synonym['hasil_manual_1'] = self.df_jawaban['nilai_manual_1']
        self.df_hasil_dengan_synonym['hasil_manual_2'] = self.df_jawaban['nilai_manual_2']
        self.df_hasil_dengan_synonym['hasil_manual_3'] = self.df_jawaban['nilai_manual_3']
        self.df_hasil_dengan_synonym['hasil_manual_4'] = self.df_jawaban['nilai_manual_4']
        self.df_hasil_dengan_synonym['hasil_manual_5'] = self.df_jawaban['nilai_manual_5']
        self.df_hasil_dengan_synonym['hasil_manual_6'] = self.df_jawaban['nilai_manual_6']
        self.df_hasil_dengan_synonym['hasil_manual_7'] = self.df_jawaban['nilai_manual_7']
        self.df_hasil_dengan_synonym['hasil_manual_8'] = self.df_jawaban['nilai_manual_8']
        self.df_hasil_dengan_synonym['hasil_manual_9'] = self.df_jawaban['nilai_manual_9']
        self.df_hasil_dengan_synonym['hasil_manual_10'] = self.df_jawaban['nilai_manual_10']
        self.df_hasil_dengan_synonym['total_nilai_ro'] = np.round((
            self.df_hasil_dengan_synonym.iloc[:, 1:11].sum(axis=1))/10, decimals=2)
        self.df_hasil_dengan_synonym['total_nilai_manual'] = np.round((
            self.df_hasil_dengan_synonym.iloc[:, 11:21].sum(axis=1))/10, decimals=2)
        # self.df_hasil_dengan_synonym.to_excel(
        # 'D:/Coding Skripsi/Hasil Pengujian Jawaban/final_hasil_ro_dengan_synonym.xlsx')
        return self.df_hasil_dengan_synonym

    def ro_tanpa_synonym(self):
        self.df_hasil_tanpa_synonym = pd.DataFrame(columns=[])
        self.df_hasil_tanpa_synonym['siswa'] = self.df_jawaban['siswa']
        self.df_hasil_tanpa_synonym['hasil_ro_1'] = self.df_jawaban['jawaban_1'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_1))
        self.df_hasil_tanpa_synonym['hasil_ro_2'] = self.df_jawaban['jawaban_2'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_2))
        self.df_hasil_tanpa_synonym['hasil_ro_3'] = self.df_jawaban['jawaban_3'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_3))
        self.df_hasil_tanpa_synonym['hasil_ro_4'] = self.df_jawaban['jawaban_4'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_4))
        self.df_hasil_tanpa_synonym['hasil_ro_5'] = self.df_jawaban['jawaban_5'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_5))
        self.df_hasil_tanpa_synonym['hasil_ro_6'] = self.df_jawaban['jawaban_6'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_6))
        self.df_hasil_tanpa_synonym['hasil_ro_7'] = self.df_jawaban['jawaban_7'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_7))
        self.df_hasil_tanpa_synonym['hasil_ro_8'] = self.df_jawaban['jawaban_8'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_8))
        self.df_hasil_tanpa_synonym['hasil_ro_9'] = self.df_jawaban['jawaban_9'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_9))
        self.df_hasil_tanpa_synonym['hasil_ro_10'] = self.df_jawaban['jawaban_10'].apply(
            lambda x: self.processing.processing_tanpa_synonym(x, self.kj_10))
        self.df_hasil_tanpa_synonym['hasil_manual_1'] = self.df_jawaban['nilai_manual_1']
        self.df_hasil_tanpa_synonym['hasil_manual_2'] = self.df_jawaban['nilai_manual_2']
        self.df_hasil_tanpa_synonym['hasil_manual_3'] = self.df_jawaban['nilai_manual_3']
        self.df_hasil_tanpa_synonym['hasil_manual_4'] = self.df_jawaban['nilai_manual_4']
        self.df_hasil_tanpa_synonym['hasil_manual_5'] = self.df_jawaban['nilai_manual_5']
        self.df_hasil_tanpa_synonym['hasil_manual_6'] = self.df_jawaban['nilai_manual_6']
        self.df_hasil_tanpa_synonym['hasil_manual_7'] = self.df_jawaban['nilai_manual_7']
        self.df_hasil_tanpa_synonym['hasil_manual_8'] = self.df_jawaban['nilai_manual_8']
        self.df_hasil_tanpa_synonym['hasil_manual_9'] = self.df_jawaban['nilai_manual_9']
        self.df_hasil_tanpa_synonym['hasil_manual_10'] = self.df_jawaban['nilai_manual_10']
        self.df_hasil_tanpa_synonym['total_nilai_ro'] = np.round((
            self.df_hasil_tanpa_synonym.iloc[:, 1:11].sum(axis=1))/10, decimals=2)
        self.df_hasil_tanpa_synonym['total_nilai_manual'] = np.round((
            self.df_hasil_tanpa_synonym.iloc[:, 11:21].sum(axis=1))/10, decimals=2)
        # self.df_hasil_tanpa_synonym.to_excel(
        #     'D:/Coding Skripsi/Hasil Pengujian Jawaban/final_hasil_ro_tanpa_synonym.xlsx')
        return self.df_hasil_tanpa_synonym


class App:
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    @ app.route('/')
    def index():
        return render_template('index.html')

    @ app.route('/demo_soal')
    def demo_soal():
        return render_template('halaman_soal.html')

    @ app.route('/hasil', methods=['POST'])
    def hasil():
        jawaban = request.form['jawaban']
        kunci_jawaban = "Volatile memory adalah memori yang datanya dapat ditulis dan dihapus, tetapi hilang saat kehilangan power."
        processing = Processing()
        nilai_tanpa_sr = processing.processing_tanpa_synonym(
            jawaban, kunci_jawaban)
        nilai_dengan_sr = processing.processing_dengan_synonym(
            jawaban, kunci_jawaban)

        return render_template('hasil.html', jawaban=jawaban, kj=kunci_jawaban, nilai_dengan_sr=nilai_dengan_sr, nilai_tanpa_sr=nilai_tanpa_sr)

    @ app.route('/tabel')
    def tabel():
        pengujian = PengujianAlgoritmaFile()
        hasil_tanpa_synonym = pengujian.ro_tanpa_synonym()
        hasil_dengan_synonym = pengujian.ro_dengan_synonym()

        df_tabel_hasil = pd.DataFrame(columns=[])
        df_tabel_hasil['siswa'] = hasil_tanpa_synonym['siswa']
        df_tabel_hasil['total_nilai_manual'] = hasil_tanpa_synonym['total_nilai_manual']
        df_tabel_hasil['total_nilai_sistem_tanpa_synonym'] = hasil_tanpa_synonym['total_nilai_ro']
        df_tabel_hasil['total_nilai_sistem_dengan_synonym'] = hasil_dengan_synonym['total_nilai_ro']
        df_tabel_hasil['mape_tanpa_sinonim'] = np.round(hasil_tanpa_synonym['total_nilai_manual'].subtract(
            hasil_tanpa_synonym['total_nilai_ro']).abs().div(df_tabel_hasil['total_nilai_manual']).mul(100), decimals=2)
        df_tabel_hasil['mape_dengan_sinonim'] = np.round(hasil_dengan_synonym['total_nilai_manual'].subtract(
            hasil_dengan_synonym['total_nilai_ro']).abs().div(df_tabel_hasil['total_nilai_manual']).mul(100), decimals=2)

        total_mape_tanpa_sinonim = np.round(
            df_tabel_hasil['mape_tanpa_sinonim'].mean(), decimals=2)
        total_mape_sinonim = np.round(
            df_tabel_hasil['mape_dengan_sinonim'].mean(), decimals=2)

        page = int(request.args.get('page', 1))

        # Menentukan jumlah baris per halaman
        rows_per_page = 10

        # Menghitung jumlah halaman berdasarkan jumlah baris
        total_pages = int((len(df_tabel_hasil) - 1) / rows_per_page) + 1

        # Memecah data berdasarkan halaman yang dipilih
        start_index = (page - 1) * rows_per_page
        end_index = start_index + rows_per_page
        data = df_tabel_hasil.iloc[start_index:end_index].to_dict(
            orient='records')

        return render_template('tabel.html', data=data, total_pages=total_pages, current_page=page, total_mape_sinonim=total_mape_sinonim, total_mape_tanpa_sinonim=total_mape_tanpa_sinonim)

    @ app.route('/upload', methods=['POST'])
    def upload_file():
        file_count = 0
        file = ['file1', 'file2']
        for f in file:
            file = request.files[f]
            if file and file.filename != '':
                file.save('D:/Coding Skripsi/' + file.filename)
                file_count += 1

        if file_count < 2:
            return 'File belum lengkap. Harap unggah 2 file.'

        return redirect(url_for('tabel'))

    # if __name__ == '__main__':
    #     app.run(debug=True)


# s = SynonymRecognition()

# kjr = "komputer rangkaian mesin elektronik dapat bekerja sama sistem digunakan memudahkan pekerjaan manusia komputer bekerja otomatis berdasarkan urutan instruksi program diberikan"
# kjw = kjr.replace(" ", "")

# jr = "komputer serangkaian ataupun sekelompok mesin elektronik terdiri ribuan bahkan jutaan komponen saling bekerja sama membentuk sebuah sistem kerja rapi teliti sistem kemudian dapat digunakan melaksanakan serangkaian pekerjaan otomatis berdasar urutan instruksi ataupun program diberikan kepadanya"
# jw = jr.replace(" ", "")
# js = s.synonym_recognition(jr, kjr).replace(" ", "")

# a = AlgoritmaRO()
# a.algoritma_ro(jw, kjw)

p = PengujianPreprocessingFile()
p.loop_preprocessing_jawaban()
