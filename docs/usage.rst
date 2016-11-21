***********
Użytkowanie
***********

Aplikacja wyposażona jest w panel administracyjny, który zapewnia możliwość wykonanie podstawowych operacji administracyjnych.

Należy w szczególności wyróżnić:
- dodawanie ankiety
  
Dodawanie instytucji
********************

.. todo:: Należy przedstawić dodawanie ``surveys.models.NationalHealthFund`` i ``surveys.models.Hospital``.

Dodawanie ankiety z wymaganymi elementami
*****************************************

 .. todo:: Należy opisać dodanie z pomocą panelu administracyjnego ``survey.models.Survey``, następnie ``survey.models.Category``, następnie ``survey.models.Question``, następnie ``survey.models.Subquestion``. Dużą część tych rzeczy można dodać z pomocą dodanych inlines, co też należy zaznaczyć. Potem dodać ``surveys.models.Participate``. Po wykonaniu tych wszystkich czynności walidacja powiedzie się. 

Wykaz uczestników
*****************

.. todo:: PRIORYTET! Na stronie xxx jest dostępny wykaz uczestników. Przedstawia on informacje o danych dostepowych dla uczestników. Po wybraniu XXX można przejść do "Pokaż na stronie". Przedstawia także  losowy kod, który domyślnie składa się tylko z cyfr. 

Wypełnienie ankiety
*******************

.. todo:: PRIORYTET! Ankieta jest powiązana z uczestnikiem (oddziałem NFZ). Adres ankiety zawiera kod, który domyślnie składa się tylko z cyfr. Poczatkowo wykaz szpitali, potem pytania. W międzyczasie powiadomienie o wypełnionej ankiecie. W przypadku działań administratora powiadomienia o wypełnieniu ankiety nie otrzymuje szpital, a tylko użytkownicy, którzy zażyczli sobie powiadomień (ref. Powiadomienia).

Statystyki
**********

.. todo:: PRIORYTET! Po wybraniu konkretnej ankiety dostepny jest przycisk "Statystyki", który prezentuje na jakim etapie dany szpital jest w wypełnianiu ankiety. Widać kto wypełnił jaką część ankiet. Jest także zbiorcze podsumowanie badania.

Żądania
*******

.. todo:: Możliwe jest przejrzenie żądań do serwera w zakładce X. Można dzięki temu 

Dodawanie użytkownika
*********************

.. todo:: Jak dodać. Ustawienia powiadomień. 

Powiadomienia
*************

.. todo:: Ustawienia powiadomień http://localhost:8000/admin/users/user/1/change/ , które decydują o tym czy użytkownik będzie dostawać powiadomienie o każdej wypełnionej ankiecie.

Eksport ankiety
***************

.. todo:: PRIORYTET! Po przejściu do ankiety jest "Eksport".
