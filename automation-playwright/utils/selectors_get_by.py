SELECTORS: dict[str, dict] = {
    "react": {
        "login_email":        "login-email",
        "login_password":     "login-password",
        "login_submit":       "login-button-visible",
        "logout":             "navbar-logout",
        "nav_cart":           "navbar-cart",
        "nav_login":          "navbar-login",
        "nav_products":       "navbar-products",
        "cart_counter":       "cart-counter",
        "product_card":       ".product-card",
        "add_to_cart":        {"role": "button", "name": "Agregar al carrito"},
        "remove_item":        "remove-item-button"
    },
    "angular": {
        "login_email":        "login-email",
        "login_password":     "login-password",
        "login_submit":       "login-submit",
        "logout":             "header-logout",
        "nav_cart":           "sidebar-cart",
        "nav_login":          "header-login",
        "nav_products":       "header-products",
        "cart_counter":       "sidebar-cart",
        "product_card":       "catalog-item-",
        "add_to_cart":        {"role": "button", "name": "Agregar"},
        "remove_item":        "cart-remove-1"
    },
    "svelte": {
        "login_email":        {"role": "textbox", "name": "Email"},
        "login_password":     {"role": "textbox", "name": "Password"},
        "login_submit":       {"role": "button", "name": "Enter"},
        "logout":             {"role": "button", "name": "Logout"},
        "nav_cart":           {"role": "link", "name": "View cart"},
        "nav_login":          {"role": "link", "name": "Login"},
        "nav_products":       {"role": "link", "name": "Products"},
        "cart_counter":       {"role": "link", "name": "View cart", "child": "strong"},
        "product_card":       {"role": "article"},
        "add_to_cart":        {"role": "button", "name": "Add to bag"},
        "remove_item":        {"role": "button", "name": "Remove"}
    },
}