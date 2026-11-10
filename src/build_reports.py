"""Generate Indonesian Word reports using actual outputs and native GUI evidence."""
from pathlib import Path
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from .data_loader import ROOT

OUT=ROOT/'outputs/reports'


def number(value,digits=3):
    return f'{float(value):,.{digits}f}'.replace(',','_').replace('.',',').replace('_','.')


def font(run,size=None,bold=None):
    run.font.name='Times New Roman';run.font.color.rgb=RGBColor(0,0,0)
    if size is not None:run.font.size=Pt(size)
    if bold is not None:run.bold=bold
    rpr=run._element.get_or_add_rPr();fonts=rpr.find(qn('w:rFonts'))
    if fonts is None:fonts=OxmlElement('w:rFonts');rpr.insert(0,fonts)
    for k in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+k),'Times New Roman')
    return run


def field(paragraph,code):
    r=paragraph.add_run();font(r,10)
    start=OxmlElement('w:fldChar');start.set(qn('w:fldCharType'),'begin')
    instruction=OxmlElement('w:instrText');instruction.set(qn('xml:space'),'preserve');instruction.text=' '+code+' '
    end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end')
    r._r.extend([start,instruction,end])


def new_document(title,subtitle):
    doc=Document();sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(2.5);sec.bottom_margin=Cm(2.5);sec.left_margin=Cm(3.0);sec.right_margin=Cm(2.5)
    sec.header_distance=Cm(1.2);sec.footer_distance=Cm(1.2);sec.different_first_page_header_footer=True
    for style in doc.styles:
        if style.type in [1,2]:
            style.font.name='Times New Roman';style.font.color.rgb=RGBColor(0,0,0)
            style.font.size=Pt(12)
    for name in ['Normal','Body Text','List Bullet','List Number']:
        s=doc.styles[name];s.paragraph_format.line_spacing=1.3;s.paragraph_format.space_after=Pt(4)
    for name,size in [('Title',18),('Subtitle',13),('Heading 1',14),('Heading 2',12),('Heading 3',12)]:
        s=doc.styles[name];s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0)
        s.paragraph_format.keep_with_next=True;s.paragraph_format.space_before=Pt(12);s.paragraph_format.space_after=Pt(6)
        if name.startswith('Heading'):s.font.bold=True
    doc.styles['Heading 1'].paragraph_format.page_break_before=True
    settings=doc.settings.element;update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');settings.append(update)
    p=sec.header.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT;font(p.add_run('Praktikum SIG | Model Garin–Lowry'),10)
    p=sec.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;font(p.add_run('Halaman '),10);field(p,'PAGE');font(p.add_run(' dari '),10);field(p,'NUMPAGES')
    doc.core_properties.title=title;doc.core_properties.subject=subtitle;doc.core_properties.author='';doc.core_properties.keywords='SIG, KNIME, Garin-Lowry, kota hipotetis, tiga pusat'
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(65)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;font(p.add_run('LAPORAN PRAKTIKUM\nSISTEM INFORMASI GEOGRAFIS'),14,True)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(40);font(p.add_run(title),18,True)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(25);font(p.add_run(subtitle),13)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(60);font(p.add_run('Case 10 dan Studi Kasus Mandiri\nKota Tiga Pusat Pekerjaan'),12)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(40);font(p.add_run('10 November 2026'),12)
    doc.add_page_break()
    return doc


def rich(paragraph,text,size=None):
    for chunk in re.split(r'(\*\*.*?\*\*)',text):
        if not chunk:continue
        bold=chunk.startswith('**') and chunk.endswith('**')
        font(paragraph.add_run(chunk[2:-2] if bold else chunk),size,bold if bold else None)


def table(doc,rows):
    t=doc.add_table(rows=1,cols=len(rows[0]));t.style='Table Grid';t.autofit=False
    for i,row in enumerate(rows):
        cells=t.rows[0].cells if i==0 else t.add_row().cells
        for cell,value in zip(cells,row):
            cell.text='';p=cell.paragraphs[0];p.paragraph_format.line_spacing=1.1;p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
            font(p.add_run(value.strip()),10.5,i==0)
        pr=t.rows[i]._tr.get_or_add_trPr();no_split=OxmlElement('w:cantSplit');pr.append(no_split)
    hdr=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(hdr)


def add_markdown(doc,content):
    lines=content.strip().splitlines();i=0;figure_no=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('#'):
            mark,text=line.split(' ',1);p=doc.add_paragraph(style=f'Heading {min(len(mark),3)}');rich(p,text);i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'[\s:\-]+',c or '-') for c in cells):rows.append(cells)
                i+=1
            table(doc,rows);continue
        image=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
        if image:
            title,path=image.groups();path=(OUT/path).resolve()
            if not path.is_file():raise FileNotFoundError(f'Required real image is missing: {path}')
            p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
            from PIL import Image
            with Image.open(path) as im:w,h=im.size
            preferred_width=13.0 if path.name=='09_convergence.png' else 15.5
            width=min(preferred_width,18.0*w/h);font(p.add_run()).add_picture(str(path),width=Cm(width))
            figure_no+=1;p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.line_spacing=1.1
            font(p.add_run(f'Gambar {figure_no}. {title}'),10.5)
            i+=1;continue
        if line.startswith('- '):
            p=doc.add_paragraph();p.paragraph_format.left_indent=Cm(.5);p.paragraph_format.first_line_indent=Cm(-.3)
            font(p.add_run('• '));rich(p,line[2:]);i+=1;continue
        if re.match(r'^\d+\. ',line):
            p=doc.add_paragraph();p.paragraph_format.left_indent=Cm(.5);p.paragraph_format.first_line_indent=Cm(-.5);rich(p,line);i+=1;continue
        paragraphs=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','|','![','- ')):
            paragraphs.append(lines[i].strip());i+=1
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;rich(p,' '.join(paragraphs))
    return figure_no


def add_toc(doc):
    p=doc.add_paragraph();font(p.add_run('DAFTAR ISI'),14,True)
    field(p,'TOC \\o "1-2" \\h \\z \\u');doc.add_page_break()


def save_report(name,title,subtitle,content,abstract=None,toc=True):
    OUT.mkdir(parents=True,exist_ok=True);doc=new_document(title,subtitle)
    if abstract:
        p=doc.add_paragraph();font(p.add_run('ABSTRAK'),14,True)
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;rich(p,abstract)
        p=doc.add_paragraph();font(p.add_run('Kata kunci: Garin–Lowry, SIG, KNIME, aksesibilitas, kota hipotetis, polisentris.'),11)
        doc.add_page_break()
    if toc:add_toc(doc)
    count=add_markdown(doc,content)
    for p in doc.paragraphs:
        for r in p.runs:font(r)
    destination=OUT/(name+'.docx');doc.save(destination)
    (OUT/(name+'.md')).write_text(content,encoding='utf8')
    return dict(file=destination.name,figures=count,paragraphs=len(doc.paragraphs),tables=len(doc.tables))


def main():
    validation=json.loads((ROOT/'outputs/logs/extended_validation.json').read_text())
    if not validation['native_execution_all_nodes'] or validation['test_failures']:
        raise RuntimeError('Native KNIME execution and tests must be verified before report generation')
    from .report_content import main_content,standalone_content,easy_content
    summary=pd.read_csv(ROOT/'outputs/tables/scenario_comparison_extended.csv')
    effects=json.loads((ROOT/'outputs/logs/custom_case_results.json').read_text(encoding='utf8'))
    abstract=('Proyek ini mereproduksi Model Garin–Lowry pada kota hipotetis menggunakan workflow KNIME Case 10 asli. '
              'Data terdiri atas 136 zona, 136 centroid, dan 330 fitur jalan. Seluruh 18.496 pasangan OD dihitung melalui jaringan, '
              'kemudian digunakan pada sistem keseimbangan (I−GT)P=GB dan S=TP. Pengembangan mempertahankan node asli dan '
              'menambahkan studi mandiri tiga pusat pekerjaan: CBD 40% dan dua satelit masing-masing 30%. Dibandingkan CBD tunggal, '
              f'penduduk CBD turun {number(abs(effects["cbd_population_change_pct"]),2)}% dan radius rata-rata berbobot bertambah '
              f'{number(effects["weighted_radius_change_m"],2)} meter proyeksi. Total penduduk sekitar 500 dan pekerjaan jasa sekitar 150 '
              'tetap karena total pekerjaan dasar serta rasio demografis dikendalikan. Versi extended memiliki 34 node dan delapan '
              f'skenario; {validation["test_count"]} tes otomatis lulus. Laporan menyertakan hasil GIS dan tangkapan layar output KNIME asli. '
              'Hasil menunjukkan perubahan alokasi spasial dalam model teoritis dan tidak ditafsirkan sebagai prediksi kota nyata.')
    outputs=[]
    outputs.append(save_report('Laporan_Garin_Lowry_KNIME_dan_Studi_Mandiri',
        'Implementasi Model Garin–Lowry pada Kota Hipotetis Menggunakan KNIME Analytics Platform',
        'Reproduksi Case 10, delapan skenario, dan pengembangan kota tiga pusat',
        main_content(summary,effects,validation,number),abstract))
    outputs.append(save_report('Studi_Kasus_Mandiri_Kota_Tiga_Pusat',
        'Studi Kasus Mandiri: Kota Tiga Pusat Pekerjaan',
        'Eksperimen distribusi pekerjaan dasar CBD 40% dan satelit 30%–30%',
        standalone_content(summary,effects,validation,number)))
    outputs.append(save_report('Penjelasan_Mudah_Project_Garin_Lowry',
        'Penjelasan Mudah Proyek Garin–Lowry',
        'Panduan memahami model, hasil, studi kasus, dan demonstrasi KNIME',
        easy_content(summary,effects,validation,number),toc=False))
    (OUT/'report_generation.json').write_text(json.dumps(outputs,indent=2),encoding='utf8')
    print(json.dumps(outputs,indent=2))


if __name__=='__main__':main()
