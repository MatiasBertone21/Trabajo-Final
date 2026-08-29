from pages.base_page import BasePage


class ProductsPage(BasePage):
    def goto(self):
        self.navigate("/products")

    def get_product_cards(self):
        return self.page.locator(self.selectors["product_card"])

    def add_to_cart(self, index: int = 0):
        self.page.locator(self.selectors["add_to_cart"]).nth(index).click()

    def add_laptop_to_cart(self, page):
        self.page = page

        self.laptop_pro_card = page.locator(".product-card").filter(has_text="Laptop Pro")

        self.laptop_pro_add_to_cart_button = self.laptop_pro_card.get_by_role(
            "button",
            name="Agregar al carrito"
        )
        self.laptop_pro_add_to_cart_button.click()

    def add_to_cart_get_by(self, index: int = 0):
        self._get_locator_by("add_to_cart").nth(index).click()
        self.page.wait_for_load_state("networkidle")

