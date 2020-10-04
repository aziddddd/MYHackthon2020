from paddleocr import PaddleOCR, draw_ocr
from difflib import SequenceMatcher
import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import re
import os

ocr = PaddleOCR(lang='en') # need to run only once to download and load model into memory

st.beta_set_page_config(
    page_title="Page Title",
    # page_icon="path/to/favicon.ico",
    # initial_sidebar_state="expanded",
)

st.set_option('deprecation.showfileUploaderEncoding', False)

def newliner(n=4, sidebar=False):
    for i in range(n):
        if sidebar:
            st.sidebar.write('\n')
        else:
            st.write('\n')

def main():
    st.sidebar.title('Jabatan Kebajikan Masyarakat Malaysia')
    st.sidebar.text('OKU Registration')
    
    form = {}
    form['Nama'] = None
    doc_path = None
    sd1, sd2, sd3, sd4, sd5, sd6 = None, None, None, None, None, None

    if st.sidebar.checkbox('Online Form'):
        st.title('Isi form di bawah ini.')
        questions = [
            'Nama',
            'Alamat [Barisan 1]',
            'Alamat [Barisan 2]',
            'Poskod dan Bandar',
            'Negeri',
            'No. I/C'
        ]

        for question in questions:
            form[question] = st.text_input(question)
            if question == 'Alamat [Barisan 2]' and form[question] == '':
                form.pop(question, None)
        if st.button('Submit'):            
            st.balloons()

    if not form['Nama']:
        st.stop()

    os.system('rm -rf resources/*')
    doc_path = 'resources/{}'.format(form['Nama'].replace(' ','').lower())
    os.mkdir(doc_path)

    if st.sidebar.checkbox('Supporting Documents'):
        newliner(n=3)
        st.title('Upload dokumen pengesahan anda.')
        sd1_label = "Salinan MyKad/ Kad Pengenalan Pemohon"
        sd2_label = "Salinan MyKad /Kad Pengenalan ahli keluarga yang tinggal bersama"
        sd3_label = "Salinan Kad OKU/ slip pendaftaran sementara OKU;(Jika Kategori OKU)"
        sd4_label = "Salinan penyata pendapatan/surat akuan pendapatan;(jika bekerja sendiri)"
        sd5_label = "Salah satu Bil Utiliti (air/elektik/telefon/Astro)"
        sd6_label = "Laporan pegawai perubatan dari hospital/klinik kesihatan kerajaan/swasta (bagi kes OKU tidak bekerja/terlantar/kronik/alat tiruan)"

        sd1 = st.file_uploader(
            label=sd1_label, 
            type=['png', 'jpg', 'jpeg', 'pdf']
        )
        sd2 = st.file_uploader(
            label=sd2_label,
            type=['png', 'jpg', 'jpeg', 'pdf']
        )

        sd3 = st.file_uploader(
            label=sd3_label,
            type=['png', 'jpg', 'jpeg', 'pdf']
        )

        sd4 = st.file_uploader(
            label=sd4_label,
            type=['png', 'jpg', 'jpeg', 'pdf']
        )

        sd5 = st.file_uploader(
            label=sd5_label,
            type=['png', 'jpg', 'jpeg', 'pdf']
        )

        sd6 = st.file_uploader(
            label=sd6_label,
            type=['png', 'jpg', 'jpeg', 'pdf']
        )

    if sd1 or sd2 or sd3 or sd4 or sd5 or sd6:
        pass
    else:
        st.stop()
    if st.sidebar.checkbox('Verification'):
        newliner(n=3)
        st.title('Proses pengesahan sedang berjalan...')
        if sd1:
            newliner(n=1)
            st.text(sd1_label)

            image = Image.open(sd1).convert('RGB')
            image_path = doc_path + '/sd1_label.png'
            image.save(image_path)
            # img_array = np.array(image)
            # st.write(type(img_array))
            # st.write(img_array)

            result = ocr.ocr(image_path)
            boxes = [line[0] for line in result]
            txts = [line[1][0] for line in result]
            scores = [line[1][1] for line in result]
            im_show = draw_ocr(image, boxes, txts, scores, font_path='fonts/simfang.ttf')
            # im_show = Image.fromarray(im_show)
            st.image(im_show, use_column_width=True)
            # for line in result:
            #     st.write(line[-1][0])
            threshold = 0.5
            verified = {
                'Field': [],
                'Answer': [],
                'Compared with': [],
                'Similarity Score': [],
            }
            for field, answer in form.items():
                high_score = None
                for line in result:
                    # st.write(line[-1][0])
                    processed_answer = answer.upper().replace(' ', '')
                    processed_line = line[-1][0].upper().replace(' ', '')
                    diff = SequenceMatcher(None, processed_answer, processed_line).ratio()
                    if high_score:
                        if diff > high_score:
                            del verified['Field'][-1]
                            del verified['Answer'][-1]
                            del verified['Compared with'][-1]
                            del verified['Similarity Score'][-1]
                            verified['Field'].append(field)
                            verified['Answer'].append(processed_answer)
                            verified['Compared with'].append(processed_line)
                            verified['Similarity Score'].append(diff)
                            high_score = diff
                            continue
                    elif diff > threshold:
                        verified['Field'].append(field)
                        verified['Answer'].append(processed_answer)
                        verified['Compared with'].append(processed_line)
                        verified['Similarity Score'].append(diff)
                        high_score = diff
                        # break
            not_verified = {field: answer for field, answer in form.items() if field not in verified['Field']}

            st.subheader('Passed')
            st.write(pd.DataFrame(verified))

            st.subheader('Not passed')
            st.write(not_verified)
            

main()