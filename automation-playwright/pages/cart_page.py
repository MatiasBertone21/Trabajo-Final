from playwright.sync_api import expect

from pages.base_page import BasePage


class CartPage(BasePage):
    def goto(self):
        self.navigate("/cart")

    def remove_item(self, index: int = 0):
        self.page.locator(self.selectors["remove_item"]).nth(index).click()
        self.page.wait_for_load_state("networkidle")

    def clear_cart(self):
        selector = self.selectors.get("clear_cart")
        if not selector:
            raise NotImplementedError("clear_cart is not available for this frontend")
        self.page.click(selector)
        self.page.wait_for_load_state("networkidle")

    def is_empty(self) -> bool:
        return self.page.locator(self.selectors["empty_cart"]).is_visible(timeout=self.timeout)

    def remove_item_get_by(self, index: int = 0):
        remove_button = self._get_locator_by("remove_item")
        expect(remove_button).to_be_visible()
        remove_button.click()
        self.page.wait_for_load_state("networkidle")
