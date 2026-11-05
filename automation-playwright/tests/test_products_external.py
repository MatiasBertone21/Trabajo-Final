import os
import pytest
from playwright.sync_api import Page
from utils.openvisor_helper import detect_for_openvisor, record_playwright_action

EXTERNAL_STORES = [
    {
        "name": "mercadolibre",
        "url": "https://www.mercadolibre.com.ar/kit-2-camaras-seguridad-geotek-3mp-ip-wifi-exterior-full-hd-domo-vision-nocturna-inteligente-deteccion-movimiento/p/MLA50438970",
        "needs_login": False,
        "target_desc": "Agregar al carrito",
        "synonyms": ["cart", "add", "carrito", "agregar"],
        "expected_min_candidates": 1,
    },
    {
        "name": "tiendamia",
        "url": "https://tiendamia.com.ar/p/amz/b0hfnc155t/15-6-inch-laptop-with-fhd-display-6gb-ram-128gb-storage",
        "needs_login": False,
        "target_desc": "Agregar al carrito",
        "synonyms": ["cart", "add", "carrito", "agregar"],
        "expected_min_candidates": 1,
    },
    {
        "name": "montagne",
        "url": "https://www.montagne.com.ar/producto/2979-campera-de-hombre-elbrus",
        "needs_login": False,
        "target_desc": "Comprar",
        "synonyms": ["cart", "add", "carrito", "agregar"],
        "expected_min_candidates": 1,
    },
    {
        "name": "movistar",
        "url": "https://tiendaonline.movistar.com.ar/apple-iphone-16e-128gb-5g.html?aux_utm_campaign=&adgroupid=&keyword=&ds_e_adid=&ds_e_matchtype=&ds_e_device=c&ds_e_network=x&ds_e_product_group_id=&ds_e_product_id=24253&ds_e_product_merchant_id=117738360&ds_e_product_country=AR&ds_e_product_language=es&ds_e_product_channel=online&ds_e_product_store_id={product_store_id}&ds_url_v=2&gclsrc=aw.ds&gad_source=1&gad_campaignid=20517989197&gbraid=0AAAAADzxJQNyKwYtArpMlFY9KtXOBZuxT&gclid=EAIaIQobChMIo4zS3tHBlwMVG2dIAB1bUA3QEAQYAiABEgIBFvD_BwE",
        "needs_login": False,
        "target_desc": "Agregar al carrito",
        "synonyms": ["cart", "add", "carrito", "agregar"],
        "expected_min_candidates": 1,
    },
    {
        "name": "amazon",
        "url": "https://www.amazon.com/TREBLAB-Auriculares-inal%C3%A1mbricos-Bluetooth-h%C3%ADbrido/dp/B0778V7RVR/ref=sr_1_1_sspa?_encoding=UTF8&content-id=amzn1.sym.a64ac9fc-2717-4051-ae96-b2a9a2a6b039&dib=eyJ2IjoiMSJ9.ZP8j3kzbknQx3w3945bbubECVvSSjoPhWuq67evoUMBNKrOfyhFIrWv3tKKtJkl2HE6_S9VGJr7UM24Rqy_4Ys6ooKJt4q4GmQQ4SoIiJiIcB3ug2470BnJVfuoa7DPoT_IjPM4X7Csz_pebtwh4ag8t7fjrp0YAOI4AG45XEvspCdhT5Nmt3OHlC5rhAnjF5UVO8H_iWFwBJupYaB521YjYQpEnl5gMNs9vY68HC8c.NFQwMSIntQSabUrTGW9UIbB3_SRFvNGalZuaJaLi4go&dib_tag=se&keywords=headphones&pd_rd_r=c5b2d888-6b30-414b-a790-d563924bd4f9&pd_rd_w=py1hp&pd_rd_wg=gddf1&qid=1792263950&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1",
        "needs_login": False,
        "target_desc": "Agregar al carrito",
        "synonyms": ["cart", "add", "carrito", "agregar"],
        "expected_min_candidates": 1,
    },
    {
        "name": "personal",
        "url": "https://www.personal.com.ar/tienda/celulares/apple/iphone-17-pro-max/f?utm_source=google&utm_medium=cpc&gad_source=1&gad_campaignid=20694534423&gbraid=0AAAAADuxtUx32FrNZXoDBe78igIQfAo22&gclid=EAIaIQobChMI5KSEsOXBlwMV3klIAB3CFwHLEAQYAiABEgLv4_D_BwE",
        "needs_login": False,
        "target_desc": "Agregar al carrito",
        "synonyms": ["cart", "add", "carrito", "agregar"],
        "expected_min_candidates": 1,
    },

]


@pytest.mark.external
@pytest.mark.opencv
@pytest.mark.parametrize("store", EXTERNAL_STORES, ids=lambda s: s["name"])
def test_detect_add_to_cart_in_external_stores(page: Page, store: dict):
    """
    Evaluate OpenVisor visual and OCR perception pipeline on external web stores.
    Tests transferability of template matching, contour detection and OCR ranking.
    """
    # 1. Navigate to target store
    if store.get("needs_login"):
        page.goto(store["url"], wait_until="networkidle", timeout=20000)
        creds = store["login_creds"]
        page.fill("#user-name", creds["user"])
        page.fill("#password", creds["pass"])
        page.click("#login-button")
        page.wait_for_load_state("networkidle")
    else:
        page.goto(store["url"], wait_until="load", timeout=20000)
        ## page.pause()

    # 2. Vision detection with 2 attempts (scroll-and-retry if not found)
    max_attempts = 2
    candidates = []
    result = {}
    audit_dir = None

    for attempt in range(1, max_attempts + 1):
        identifier = f"external-{store['name']}-attempt-{attempt}"
        result = detect_for_openvisor(
            page,
            target_description=store["target_desc"],
            element_type="button",
            synonyms=store["synonyms"],
            enable_ocr=True,
            visual_threshold=0.6,
            identifier=identifier
        )

        audit_dir = result.get("audit_dir")
        candidates = result.get("candidates", [])
        print(f"\n[OpenVisor External] {store['name']} (Attempt {attempt}/{max_attempts}): {len(candidates)} candidates detected.")

        if candidates:
            break

        # If no candidates and we have another attempt, scroll down to reveal more content
        if attempt < max_attempts:
            print(f"[OpenVisor External] No candidates on attempt {attempt}. Scrolling down 400px...")
            page.mouse.wheel(0, 100)
            page.wait_for_timeout(1000)

    # 3. Assert detection results
    if not candidates:
        record_playwright_action(
            audit_dir=audit_dir,
            candidate=None,
            action="none",
            status="failed",
            error=f"No candidates detected after {max_attempts} attempts for description='{store['target_desc']}'"
        )
        raise AssertionError(
            f"OpenVisor could not detect any candidate on {store['url']} with description='{store['target_desc']}' after {max_attempts} attempts"
        )

    assert len(candidates) >= store["expected_min_candidates"], (
        f"Expected at least {store['expected_min_candidates']} candidate(s), found {len(candidates)}"
    )

    # 4. Extract viewport coordinates from best candidate
    best_candidate = candidates[0]
    center = best_candidate.get("center_point", {})
    x = center.get("x")
    y = center.get("y")

    assert x is not None and y is not None, "Detected candidate missing center_point coordinates"

    # 5. Record action and click directly on viewport coordinates
    record_playwright_action(
        audit_dir=audit_dir,
        candidate=best_candidate,
        action="click",
        index=0,
        status="success"
    )

    page.mouse.click(x, y)


