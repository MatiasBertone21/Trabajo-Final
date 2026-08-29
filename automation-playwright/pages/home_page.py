from pages.base_page import BasePage


class HomePage(BasePage):
    def goto(self):
        self.navigate("/")

    def is_loaded(self) -> bool:
        return self.page.locator(self.selectors["home_page"]).is_visible()

