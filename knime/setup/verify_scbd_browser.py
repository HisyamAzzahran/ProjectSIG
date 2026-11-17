"""Optional browser check. Install playwright; run the SCBD localhost server first."""
from pathlib import Path
import json
import os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
folder=ROOT/'outputs/scbd_jakarta'
errors=[]
with sync_playwright() as p:
    configured=os.environ.get('SCBD_CHROMIUM')
    browser=p.chromium.launch(headless=True,**({'executable_path':configured} if configured else {}))
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765/SCBD_Jakarta_Live.html',wait_until='networkidle',timeout=60000)
    page.wait_for_function('window.scbdZoneLayer && scbdZoneLayer.getLayers().length===81')
    assert page.evaluate('currentScenario')=='scbd_terpusat'
    page.screenshot(path=str(folder/'01_peta_SCBD_Jakarta.png'),full_page=True)
    page.select_option('#scenario','tiga_pusat')
    assert page.evaluate('currentScenario')=='tiga_pusat'
    page.select_option('#metric','basic_employment')
    assert 'Pekerjaan dasar' in page.locator('#legendTitle').inner_text()
    page.evaluate('() => {scbdZoneLayer.getLayers()[40].openPopup(); return true;}')
    assert 'Zona 41' in page.locator('.leaflet-popup-content').inner_text()
    page.wait_for_timeout(500)
    page.screenshot(path=str(folder/'02_skenario_tiga_pusat.png'),full_page=True)
    tiles=page.locator('img.leaflet-tile-loaded').count()
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(500)
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    page.screenshot(path=str(folder/'03_peta_mobile.png'),full_page=True)
    assert not errors,errors
    evidence={'browser':'Chromium / Playwright','zones':81,
              'roads':page.evaluate('scbdRoadLayer.getLayers().length'),
              'loaded_basemap_tiles':tiles,'page_errors':errors,'scenario_selector':'passed',
              'metric_selector':'passed','popup':'passed','mobile_no_horizontal_overflow':True}
    (folder/'browser_validation.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2));browser.close()
