************
Architektura
************

Struktura kodu
************************
Aplikacja zbudowana jest z wykorzystaniem frameworka Django w języku Python. Wspierana jest silnikiem bazodanowym. Zapewnia się kompatybilność z MySQL.

Głównym modułem aplikacji jest ``survey``, który zawiera elementy charakterystyczne dla frameworka Django:

- ``admin`` - określa panel administracyjny modułu,
- ``apps`` - sztywne ustawienia modułu Django,
- ``factories`` - definicje generowania obiektów modelu danych tzw. fabryki,
- ``forms`` - formularze aplikacji.
- ``middleware`` -``middleware`` związane z funkcjonowaniem aplikacji.
- ``models`` - model danych,
- ``tests`` - różnorakie automatyczne testy komponentów aplikacji,
- ``urls`` - konfiguracja adresów (routingu),
- ``views`` - widoki wykorzystywane w aplikacji.
- ``migrations`` - migracje przedstawiające sposób aktualizacji bazy danych wraz z rozwojem aplikaci.

Istnieje także katalog ``templates``, który zawiera szablony HTML dla aplikacji i ``locale``, który zawiera pliki językowe.

Struktura modelu
****************

Najważniejszym elementem modelu jest ``survey.models.Survey``, który definiuje obiekt ankiety, w tym pola tekstowe pomocy dla ankiety. Z drugiej strony znajduje się ``survey.models.NationalHealtFund``, który definiuje oddział Narodowego Funduszu Zdrowia. 

Każda ankieta składa się z kilku uczestników (``survey.models.Participant``) reprezentujących oddział Narodowego Funduszu Zdrowia, którzy są przypisani do danej ankiety. 

Opisana jest także z pomocą kategorii pytań (``survey.models.Category``), która następnie rozwija się w pytania (``survey.models.Question``), które następnie rozwijają się w podpytania (``survey.models.Subquestion``). I dopiero w tym miejscu można wskazać, że odpowiedź jest określona poprzez podpytanie, uczestnika i szpital. Odpowiedź może odnosić się tylko do podpytania.


Dokumentacja modelu
*******************

.. automodule:: survey.models
    :members:
