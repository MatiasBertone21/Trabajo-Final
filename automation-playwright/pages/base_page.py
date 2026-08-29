import re
from playwright.sync_api import expect

class BasePage:
    def __init__(self, page, base_url: str, selectors: dict):
        self.page = page
        self.base_url = base_url
        self.selectors = selectors
        self.timeout = 8000

    def navigate(self, path: str = "/"):
        self.page.goto(f"{self.base_url}{path}")
        self.page.wait_for_load_state("networkidle")

    def get_title(self) -> str:
        return self.page.title()
    
    def expect_cart_count(self, expected: int):
        badge = self.page.locator(self.selectors["cart_counter"])
        
        expect(badge).to_be_visible()
        expect(badge).to_contain_text(str(expected))

    def go_to_cart(self):
        self.page.locator(self.selectors["nav_cart"]).click()
        self.page.wait_for_load_state("networkidle")

    def go_to_products(self):
        self.page.locator(self.selectors["nav_products"]).click()
        self.page.wait_for_load_state("networkidle")

    def go_to_login(self):
        self.page.locator(self.selectors["nav_login"]).click()
        self.page.wait_for_load_state("networkidle")

    def logout(self):
        self.page.locator(self.selectors["logout"]).click()
        self.page.wait_for_load_state("networkidle")

    # --------------------------------------------------------
    # --------------------------- get by strategy -----------------------------
    # --------------------------------------------------------

    def _get_locator_by(self, selector_key: str):
        """Resolves the locator natively using get_by_role or get_by_test_id"""
        config = self.selectors[selector_key]
        
        # Case 1: Selector is defined as a dictionary (uses get_by_role)
        if isinstance(config, dict):
            role = config["role"]
            name = config.get("name")
            if name:
                locator = self.page.get_by_role(role, name=name)
            else:
                locator = self.page.get_by_role(role)
            # support for child locator if specified
            if "child" in config:
                locator = locator.locator(config["child"])
            return locator 
        
        # Case 2: Selector is defined as a string (uses get_by_test_id)
        else:
            by_test = self.page.get_by_test_id(config)
            if by_test.count() > 0:
                return by_test.nth(0)
            return self.page.get_by_test_id(config)

    def expect_cart_count_get_by(self, expected: int):
        badge = self._get_locator_by("cart_counter")
        
        expect(badge).to_be_visible()
        expect(badge).to_contain_text(str(expected))

    def go_to_login_get_by(self):
        self._get_locator_by("nav_login").click()
        self.page.wait_for_load_state("networkidle")

    def go_to_cart_get_by(self):
        self._get_locator_by("nav_cart").click()
        self.page.wait_for_load_state("networkidle")

    def go_to_products_get_by(self):
        self._get_locator_by("nav_products").click()
        self.page.wait_for_load_state("networkidle")

    def logout_get_by(self):
        self._get_locator_by("logout").click()
        self.page.wait_for_load_state("networkidle")
