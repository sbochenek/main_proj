



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
                                    }
                                    """


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

tmp = 1