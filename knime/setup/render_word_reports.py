"""Update real Word fields/TOCs and export the generated reports to PDF."""
from pathlib import Path
import json
import win32com.client

ROOT=Path(__file__).resolve().parents[2]


def main():
    folder=ROOT/'outputs/reports';manifest=[]
    word=win32com.client.DispatchEx('Word.Application')
    word.Visible=False;word.DisplayAlerts=0
    try:
        for item in json.loads((folder/'report_generation.json').read_text()):
            path=(folder/item['file']).resolve()
            document=word.Documents.Open(str(path),ReadOnly=False,AddToRecentFiles=False)
            try:
                document.Fields.Update()
                for index in range(1,document.TablesOfContents.Count+1):document.TablesOfContents(index).Update()
                # Keep every body/TOC run black and Times New Roman after Word
                # regenerates links. Sizes, bold, tables and heading styles stay.
                document.Content.Font.Name='Times New Roman';document.Content.Font.Color=0
                document.Content.ParagraphFormat.WidowControl=True
                for section in document.Sections:
                    for h in section.Headers:
                        h.Range.Font.Name='Times New Roman';h.Range.Font.Color=0
                    for f in section.Footers:
                        f.Range.Font.Name='Times New Roman';f.Range.Font.Color=0;f.Range.Fields.Update()
                document.Repaginate()
                document.Fields.Update()
                for index in range(1,document.TablesOfContents.Count+1):document.TablesOfContents(index).UpdatePageNumbers()
                document.Save()
                pdf=path.with_suffix('.pdf')
                document.ExportAsFixedFormat(OutputFileName=str(pdf),ExportFormat=17,OpenAfterExport=False,
                                             OptimizeFor=0,Range=0,Item=0,IncludeDocProps=True,
                                             CreateBookmarks=1,DocStructureTags=True,BitmapMissingFonts=True)
                manifest.append(dict(docx=path.name,pdf=pdf.name,pages=document.ComputeStatistics(2),
                                     figures=item['figures'],tables=item['tables'],word_version=word.Version))
                print(json.dumps(manifest[-1]),flush=True)
            finally:document.Close(SaveChanges=0)
    finally:word.Quit()
    (folder/'word_render_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')


if __name__=='__main__':main()
