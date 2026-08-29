from pages.base_page import BasePage


class LoginPage(BasePage):
    def goto(self):
        self.navigate("/login")

    def fill_credentials(self, email: str, password: str):
        self.page.fill(self.selectors["login_email"], email)
        self.page.fill(self.selectors["login_password"], password)

    def submit(self):
        self.page.click(self.selectors["login_submit"])

    def is_redirected_to_home(self) -> bool:
        self.page.wait_for_url(f"{self.base_url}/", timeout=self.timeout)
        return self.page.url == f"{self.base_url}/"

    def get_error_message(self) -> str:
        for selector in [".form-error", "[role=alert]", ".error"]:
            el = self.page.locator(selector)
            if el.count() > 0:
                return el.first.inner_text()
        return ""

    def fill_login_form_get_by(self, email: str, password: str):
            self._get_locator_by("login_email").fill(email)
            self._get_locator_by("login_password").fill(password)

    def submit_get_by(self):
        self._get_locator_by("login_submit").click()
