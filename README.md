# Sztuczna Inteligencja w Robotyce - projekt
### Projekt do śledzenia przechodniów na podstawie zdjęć oraz plików tekstowych zawierających informacje o bounding boxach

Uruchamiając system należy podać ścieżkę do lokalizacji, w której znajduje się folder 'frames' zawierający badane zdjęcia oraz odpowiadający badanym zdjęciom plik 'bboxes.txt'. 
Przykład wywołania:

- `python3 main.py path/to/dataset`

Wszystkie zdjęcia wczytywane są przez program do słownika, w którym kluczami są nazwy zdjęć, a danymi same zdjęcia. Plik tekstowy 'bboxes.txt' wczytywany jest jako lista, w której elementami są kolejne linijki tekstu. Program sprawdza każdą linię po kolei i kiedy natrafi na nazwę zdjęcia znajdującego sie w słowniku zaczyna przetwarzanie. Z pliku sczytywana jest ilość bounding boxów, współrzędne ich górnego lewego wierzchołka, szerokości oraz wysokości. Posiadając te dane można rozpocząć przetwarzanie. 

Aby móc śledzić przechodniów konieczne jest wskazanie jakichś cech, na podstawie których bounding boxy będą ze sobą porównywane. W tym programie wykorzystano dwie zależności: 
1. Histogramy - są to histogramy zawierające w sobie wszystkie 3 składowe przestrzeni kolorów BGR. W celu porównywania są także normalizowane.
2. Stosunki szerokości/wysokości bounding boxów.

Dla pierwszego wczytanego zdjęcia program oblicza histogramy oraz stosunki, ale nie wykonuje żadnych dodatkowych kroków, ponieważ nie istnieje możliwość porównania. Na wyjście podawane są wartości '-1' dla każdej osoby wykrytej na klatce.

Dla każdego kolejnego zdjęcia także obliczane są obie wspomniane cechy. Wykorzystując funkcję do porównywania histogramów oraz dzielenie dla stosunków boków można wyliczyć jak podobne do siebie są bounding boxy z poprzedzającej klatki do aktualnej. Aby reprezentować podobieństwo za pomocą pojedynczej wartości, brana jest średnia z obu cech. Konieczne jest obliczenie podobieństwa każdego boxa z klatki poprzedniej do każdego boxa z klatki aktualnej. W celu wygody dostępu oraz wizualizacji wszystkie podobieństwa zapisywane są w macierzy, w której rzędy odpowiadają aktualnemu zdjęciu, a kolumny zdjęciu poprzedniemu. Przykładowo, aby odwołać się podobieństwa boxa 1 z aktualnego zdjęcia do boxa 2 z poprzedniego zdjęcia należy wczytać element z wiersza nr 1 i kolumny nr 2.

<img src="https://github.com/cezarywawrzyniak/pedestrian_tracking_project/blob/main/drawings/mt1.png" width=80% height=80%>

Samo śledzenie przechodniów odbywa się przy pomocy modelu grafu czynników zbudowanego przy pomocy modułu FactorGraph z biblioteki pgmpy. Węzłami w grafie (oraz zmiennymi losowymi) są prostokąty ograniczające się na aktualnym zdjęciu. Do każdego z nich przypisany jest czynnik zawierający prawdopodobieństwa, że dany prostokąt jest którymś z prostokątów z poprzedniej klatko oraz prawdopodobieństwo, że jest to całkowicie nowy przechodzień. Należy dodać także krawędzie łączące czynniki z węzłami. W celu prawidłowego działania wymagane są także połączenia pomiędzy węzłami na aktualnym zdjęciu. Pomiędzy tymi połączeniami dodane są czynniki uniemożliwiające przypisanie 2 aktualnych bounding boxów do jednego prostokąta z poprzedniej klatki: 

<img src="hhttps://github.com/cezarywawrzyniak/pedestrian_tracking_project/blob/main/drawings/mt2.png" width=40% height=40%>

- Rysunek grafu:
<img src="https://github.com/cezarywawrzyniak/pedestrian_tracking_project/blob/main/drawings/fg.png" width=65% height=65%>

Do ostatecznego wnioskowania wykorzystywany jest algorytm BeliefPropagation także z biblioteki pgmpy. Na wyjście programu podawane są po kolei numery prostokątów z klatki poprzedniej do której przypisane zostały aktualne prostokąty (wartość '-1' oznacza nowe obiekty)

W celu porównania działania modelu grafowego na końcu programu zaimplementowany został prosty zachłanny algorytm, który przypisuje prostokąty wprost na podstawie najlepszych dopasowań. Aby sprawdzić jego działanie wystarczy jedynie odkomentować linijkę kodu odpowiedzialną za printowanie wyjściowej listy.
