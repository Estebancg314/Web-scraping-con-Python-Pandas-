import requests
from bs4 import BeautifulSoup
import pandas as pd
import time


BASE_URL = 'http://books.toscrape.com/'
CATALOGUE_URL = 'http://books.toscrape.com/catalogue/'

def parse_price(price_str):
    """Convierte el string de precio (ej. '£51.77') a un número flotante."""
    return float(price_str.replace('£', '').replace('Â', ''))

def parse_rating(rating_class):
    """Convierte la clase de rating (ej. 'star-rating Three') a un número entero."""
    rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}

    return rating_map.get(rating_class[1], 0)

def scrape_all_books():
    """
    Navega por todas las páginas del catálogo, extrae la información de cada libro
    y la devuelve en una lista de diccionarios.
    """
    print("Iniciando el scraping de books.toscrape.com...")
    print("Esto puede tardar unos minutos, ya que se analizarán 1000 libros.")

    all_books = []
    page_url = f'{CATALOGUE_URL}page-1.html'
    page_count = 1

    while page_url:
        print(f"Analizando página {page_count}...")
        response = requests.get(page_url)

        if response.status_code != 200:
            print(f"Error al acceder a la página {page_count}. Deteniendo.")
            break

        soup = BeautifulSoup(response.content, 'html.parser')


        books_on_page = soup.find_all('article', class_='product_pod')

        for book in books_on_page:

            book_relative_url = book.find('h3').find('a')['href']
            book_full_url = f"{CATALOGUE_URL}{book_relative_url}"


            book_response = requests.get(book_full_url)
            book_soup = BeautifulSoup(book_response.content, 'html.parser')


            title = book_soup.find('h1').text
            price = parse_price(book_soup.find('p', class_='price_color').text)
            availability_text = book_soup.find('p', class_='instock availability').text.strip()

            availability = "Disponible" if 'In stock' in availability_text else "Agotado"
            rating = parse_rating(book_soup.find('p', class_='star-rating')['class'])

            genre = book_soup.find('ul', class_='breadcrumb').find_all('a')[2].text

            all_books.append({
                'Título': title,
                'Género': genre,
                'Precio (£)': price,
                'Rating (1-5)': rating,
                'Disponibilidad': availability
            })

        # Buscar el botón 'siguiente' para la paginación
        next_button = soup.find('li', class_='next')
        if next_button:
            next_page_relative_url = next_button.find('a')['href']
            page_url = f"{CATALOGUE_URL}{next_page_relative_url}"
            page_count += 1
        else:
            page_url = None 

    print("\n Scraping completado con éxito.")
    return all_books

def main_menu(df):
    """
    Muestra un menú interactivo para que el usuario filtre los datos del DataFrame
    y pueda exportar la vista actual a un archivo Excel.
    """

    current_view_df = df.copy() 

    while True:
        print("\n--- MENÚ DE FILTROS ---")
        print("1. Filtrar por Género")
        print("2. Filtrar por Calificación (Score)")
        print("3. Filtrar por Disponibilidad")
        print("4. Filtrar por Rango de Precios")
        print("5. ¿Cuántos libros hay disponibles en total?")
        print("6. Mostrar todos los libros (resetear filtros)")
        print("---------------------------------")
        print("7. Exportar vista actual a Excel") 
        print("8. Salir") 

        choice = input("Elige una opción: ")

        if choice == '1':
            print("\nGéneros disponibles:")
            genres = df['Género'].unique()
            for i, genre in enumerate(genres):
                print(f"{i+1}. {genre}")
            try:
                genre_choice_num = int(input("Ingresa el número del género que quieres ver: "))
                if 1 <= genre_choice_num <= len(genres):
                    selected_genre = genres[genre_choice_num-1]
                    print(f"\n--- Libros de Género: {selected_genre} ---")
                    current_view_df = df[df['Género'] == selected_genre] 
                    print(current_view_df.to_string())
                else:
                    print("Número de género no válido.")
            except (ValueError, IndexError):
                print("Entrada no válida. Por favor, ingresa un número de la lista.")

        elif choice == '2':
            try:
                min_rating = int(input("Ingresa la calificación mínima (1-5): "))
                if 1 <= min_rating <= 5:
                    print(f"\n--- Libros con Calificación >= {min_rating} estrellas ---")
                    current_view_df = df[df['Rating (1-5)'] >= min_rating] 
                    print(current_view_df.to_string())
                else:
                    print("Calificación no válida.")
            except ValueError:
                print("Entrada no válida. Ingresa un número entero.")

        elif choice == '3':

            print("\n--- Filtrar por Disponibilidad ---")
            print("1. Mostrar libros Disponibles")
            print("2. Mostrar libros Agotados")
            status_choice = input("Elige una opción: ")
            if status_choice == '1':
                current_view_df = df[df['Disponibilidad'] == 'Disponible']
                print(current_view_df.to_string())
            elif status_choice == '2':
                current_view_df = df[df['Disponibilidad'] == 'Agotado']
                print(current_view_df.to_string())
            else:
                print("Opción no válida.")

        elif choice == '4':
            try:
                min_price = float(input("Ingresa el precio mínimo (£): "))
                max_price = float(input("Ingresa el precio máximo (£): "))
                result = df[(df['Precio (£)'] >= min_price) & (df['Precio (£)'] <= max_price)]
                print(f"\n--- Libros entre £{min_price:.2f} y £{max_price:.2f} ---")
                current_view_df = result 
                if result.empty:
                    print("No se encontraron libros en ese rango de precios.")
                else:
                    print(result.to_string())
            except ValueError:
                print("Entrada no válida. Ingresa un número.")

        elif choice == '5':
            available_count = len(df[df['Disponibilidad'] == 'Disponible'])
            print(f"\nRespuesta: Hay {available_count} libros disponibles para comprar.")

        elif choice == '6':
            print("\n--- Mostrando todos los libros (filtros reseteados) ---")
            current_view_df = df.copy() 
            print(current_view_df.to_string())

        elif choice == '7': 
            filename = input("Ingresa el nombre para el archivo Excel (ej: libros_filtrados.xlsx): ")
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'

            try:

                current_view_df.to_excel(filename, index=False)
                print(f"\n ¡Datos exportados con éxito en el archivo '{filename}'!")
            except Exception as e:
                print(f"\n Ocurrió un error al exportar: {e}")

        elif choice == '8': 
            print("¡Hasta luego!")
            break

        else:
            print("Opción no válida. Por favor, intenta de nuevo.")


        if choice not in ['5', '7', '8']: 
             input("\nPresiona Enter para continuar...")

if __name__ == '__main__':

    books_data = scrape_all_books()


    if books_data:
        libros_df = pd.DataFrame(books_data)
        print("\n DataFrame creado con la información de los libros.")


        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)


        main_menu(libros_df)
    else:
        print("No se pudo extraer ningún dato. El programa terminará.")
