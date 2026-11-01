

SCROLL_BAR_STYLE = """
                                    /* 1. Główny tory paska pionowego */
                                    QScrollBar:vertical {
                                        border: none;
                                        background: #2b2b2b;       /* Kolor tła całego paska */
                                        width: 12px;               /* Szerokość paska */
                                        margin: 0px 0px 0px 0px;   /* Bez marginesów na strzałki */
                                        border-radius: 6px;
                                    }

                                    /* 2. Uchwyt / Suwak */
                                    QScrollBar::handle:vertical {
                                        background: #555555;       /* Kolor suwaka */
                                        min-height: 20px;          /* Minimalna wysokość suwaka */
                                        border-radius: 6px;        /* Zaokrąglone rogi */
                                    }

                                    /* Stan najechania myszką na suwak */
                                    QScrollBar::handle:vertical:hover {
                                        background: #007acc;       /* Zmiana koloru po najechaniu */
                                    }

                                    /* Stan kliknięcia suwaka */
                                    QScrollBar::handle:vertical:pressed {
                                        background: #005999;
                                    }

                                    /* 3. Ukrycie przycisków góra/dół (strzałek) */
                                    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                                        border: none;
                                        background: none;
                                        height: 0px;
                                    }

                                    /* 4. Tło toru (nad i pod suwakiem) */
                                    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
                                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                        background: none;
                                    }"""

QLIST_WIDGET_STYLE = """
                                    /* 1. Główny tory paska pionowego */
                                    QScrollBar:vertical {
                                        border: none;
                                        background: #2b2b2b;       /* Kolor tła całego paska */
                                        width: 12px;               /* Szerokość paska */
                                        margin: 0px 0px 0px 0px;   /* Bez marginesów na strzałki */
                                        border-radius: 6px;
                                    }

                                    /* 2. Uchwyt / Suwak */
                                    QScrollBar::handle:vertical {
                                        background: #555555;       /* Kolor suwaka */
                                        min-height: 20px;          /* Minimalna wysokość suwaka */
                                        border-radius: 6px;        /* Zaokrąglone rogi */
                                    }

                                    /* Stan najechania myszką na suwak */
                                    QScrollBar::handle:vertical:hover {
                                        background: #007acc;       /* Zmiana koloru po najechaniu */
                                    }

                                    /* Stan kliknięcia suwaka */
                                    QScrollBar::handle:vertical:pressed {
                                        background: #005999;
                                    }

                                    /* 3. Ukrycie przycisków góra/dół (strzałek) */
                                    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                                        border: none;
                                        background: none;
                                        height: 0px;
                                    }

                                    /* 4. Tło toru (nad i pod suwakiem) */
                                    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
                                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                        background: none;
                                    }

                                    QListWidget::item {
                                        color: white;
                                        background-color: #37393b;
                                        padding: 8px 10px;
                                        margin: 2px 5px;
                                        border-radius: 6px;
                                        outline: none;
                                    }

                                    QListWidget::item:hover {
                                        background-color: #45484a;
                                        color: white;
                                    }

                                    QListWidget::item:selected {
                                        background-color: #007acc;
                                        color: white;
                                        font-weight: normal;
                                        outline: none;
                                    }"""


SLIDER_STYLE = """
    /* 1. Tor, po którym porusza się suwak */
    QSlider::groove:horizontal {
        border: none;
        background: #2b2b2b;        /* Tło toru (analogiczne do paska) */
        height: 6px;                /* Grubości toru */
        border-radius: 3px;
    }

    /* 2. Suwak (uchwyt, którym poruszamy) */
    QSlider::handle:horizontal {
        background: #555555;        /* Kolor suwaka */
        border: none;
        width: 16px;                /* Szerokość uchwytu */
        height: 16px;               /* Wysokość uchwytu */
        margin: -5px 0;             /* Wyśrodkowanie uchwytu względem toru */
        border-radius: 8px;         /* Okrągły kształt */
    }

    /* Stan najechania myszką na suwak */
    QSlider::handle:horizontal:hover {
        background: #007acc;        /* Kolor akcentu (niebieski) */
    }

    /* Stan kliknięcia suwaka */
    QSlider::handle:horizontal:pressed {
        background: #005999;
    }
    
    /* Część toru już "zaliczona" (opcjonalnie - podświetlenie lewej strony) */
    QSlider::sub-page:horizontal {
        background: #007acc;
        border-radius: 3px;
    }
"""

OPTIONS_CONTAINER_STYLE = """
    QFrame#options_container {
        background-color: #37393b;
        border: 1px solid #45484a;
        border-radius: 10px;
    }
"""

CHECKBOX_STYLE = """
    QCheckBox {
        color: white;
        font-size: 11pt;
        spacing: 10px;
        padding: 4px;
        background-color: transparent;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid #777777;
        background-color: #2b2b2b;
    }

    QCheckBox::indicator:hover {
        border: 2px solid #007acc;
    }

    QCheckBox::indicator:checked {
        background-color: #007acc;
        border: 2px solid #007acc;
    }

    QCheckBox::indicator:checked:hover {
        background-color: #008ee6;
        border: 2px solid #008ee6;
    }

    QCheckBox:disabled {
        color: #777777;
    }
"""