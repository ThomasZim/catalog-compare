"""Point d'entrée du comparateur de catalogues."""

from .gui import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
