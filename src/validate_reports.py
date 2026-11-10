"""Inspect final PDF layout, black Times New Roman text and figure integrity."""
from pathlib import Path
import json
import re
import pymupdf
from .data_loader import ROOT


def main():
    folder=ROOT/'outputs/reports';qa=[]
    for item in json.loads((folder/'word_render_manifest.json').read_text()):
        pdf=folder/item['pdf'];document=pymupdf.open(pdf)
        fonts=set();colors=set();captions=[];problems=[];pages=[];full_text=''
        for i,page in enumerate(document):
            text=page.get_text();full_text+=text
            found=[int(n) for n in re.findall(r'Gambar\s+(\d+)\.',text)]
            captions.extend(found);images=len(page.get_images())
            if len(found)>images:problems.append(f'Caption without image on page {i+1}')
            if len(text.strip())<70 and images==0:problems.append(f'Nearly empty page {i+1}')
            for block in page.get_text('dict')['blocks']:
                if block.get('type')!=0:continue
                for line in block['lines']:
                    for span in line['spans']:
                        fonts.add(span['font']);colors.add(span['color'])
                        x0,y0,x1,y1=span['bbox']
                        if x0<12 or x1>page.rect.width-12 or y0<8 or y1>page.rect.height-8:
                            problems.append(f'Text outside page bounds on page {i+1}: '+span['text'][:40])
            pages.append(dict(page=i+1,chars=len(text),images=images))
        if captions!=list(range(1,item['figures']+1)):problems.append('Incomplete or unordered figure captions')
        if colors!={0}:problems.append('Nonblack document text')
        if not all(f.startswith('TimesNewRoman') for f in fonts):problems.append('Unexpected document font')
        if '[ISI' in full_text or 'Error! Bookmark' in full_text:problems.append('Unresolved template content or field error')
        assert not problems,(pdf.name,problems)
        qa.append(dict(pdf=pdf.name,pages=len(document),font_names=sorted(fonts),text_colors_rgb_int=sorted(colors),
                       font_scope='Selectable document text; authentic screenshot UI fonts remain unmodified',
                       figures=len(captions),layout_problems=problems,page_details=pages))
    (folder/'REPORT_QA.json').write_text(json.dumps(qa,indent=2),encoding='utf8')
    print(json.dumps([{k:v for k,v in q.items() if k!='page_details'} for q in qa],indent=2))


if __name__=='__main__':main()
