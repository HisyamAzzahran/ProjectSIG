"""Paste into a NEW Python View branch; do not replace the validated original nodes.

Set a String Configuration flow variable named scbd_project_root to the directory
containing README.md and src/scbd_case.py in this repository. Use the project venv.
This adapter is supplied for GUI verification, not claimed as an executed workflow.
"""
from pathlib import Path
import base64
import knime.scripting.io as knio

if 'scbd_project_root' not in knio.flow_variables:
    raise ValueError('Set scbd_project_root to the local Case10_Garin_Lowry_Project folder')
project=Path(knio.flow_variables['scbd_project_root'])
folder=project/'outputs/scbd_jakarta'
html=(folder/'SCBD_Jakarta_Live.html').read_text(encoding='utf8')
css=(folder/'assets/leaflet.css').read_text(encoding='utf8')
for filename in ['layers.png','layers-2x.png']:
    encoded=base64.b64encode((folder/'assets/images'/filename).read_bytes()).decode('ascii')
    css=css.replace('images/'+filename,'data:image/png;base64,'+encoded)
html=html.replace('<link rel="stylesheet" href="assets/leaflet.css">',
                  '<style>'+css+'</style>')
html=html.replace('<script src="assets/leaflet.js"></script>',
                  '<script>'+(folder/'assets/leaflet.js').read_text(encoding='utf8')+'</script>')
# Embedded KNIME pages have no CSV-relative URL. The same files are available in the project outputs.
html=html.replace('<a href="scenario_summary.csv">Unduh ringkasan CSV</a> · <a href="provenance.json">Sumber dan batasan</a>',
                  'CSV dan sumber: outputs/scbd_jakarta pada folder proyek')
knio.output_view=knio.view_html(html)
