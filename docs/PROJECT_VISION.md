# Project Vision

## TITLU TEMA: Identificarea stirilor false(fake news) din retelele de socializare, folosind algoritmi de invatare automata

Aici este o lista cu potentialele derivari ale proiectului de licenta, si in ce directii poate merge interpretarea titlului licentei:

- studierea aprofundata a algoritmilor de clasificare
    - clasificarea stirilor folosind mai multi algoritmi generici de clasificare text (Liner Regression, ANN, RNN - LSTM, Transformers - BERT, ELECTRA, RoBERTa, GPT-2)
    - compararea rezultatelor obtinute folosind metrici diverse (acuratete, precizie)
    - documentarea detaliata a metodelor de data-preprocessing (good practice to preprocess data)
    - documentarea detaliata a algoritmilor folositi - in special transformatorilor (good practice to train and test models)

- realizarea unei solutii software de tip arhitectura client-sever pentru realizarea predictiei unei stiri - partea DEMO a proiectului - *ALMOST DONE*
    - folosire cluster kubernetes pentru deployment infrastructura
        - baza de date NoSQL - MongoDB
        - server Django
    - folosirea serviciilor de monitorizare cluster (Prometheus, Loki, Promtail, Grafana)
    - documentare deployment - rolul fiecarui microserviciu in sistem

- realizarea generarii de stiri false folosind transformatori generativi - GPT-2
- realizare scrapper date pentru site-uri limba romana (deoarece trebuie din retelele de socializare, aici va trebui exista o mica filtrare a url-irlor inainte)
    - dezvoltarea unor scripturi specifice fiecarui site in parte care sa poata face extragere de date de tipul FAKE sau TRUE NEWS
        - FAKE NEWS - [Times New Roman](https://www.timesnewroman.ro)
        - TRUE NEWS - [BIZIDAY](https://www.biziday.ro), Facebook: [guv.ro](https://www.facebook.com/guv.ro), [Ministerul Sănătăţii - România](https://www.facebook.com/MinisterulSanatatii) si altele
