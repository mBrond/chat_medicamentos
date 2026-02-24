# Chatbot de Medicamentos
Trabalho realizado dentro do Programa de Educação Tutorial (PET) Saúde Digital, da Universidade Federal de Santa Maria (UFSM).

Sistema simples de chat construído em Django que responde perguntas sobre medicamentos e indica pontos de retirada na rede de saúde de Santa Maria - RS

Este trabalho apresenta o desenvolvimento de uma aplicação web que integra georreferenciamento de farmácias, agente conversacional simplificado e visualização de mapas interativos. Uma solução centralizada para reduzir o tempo de busca dos cidadãos e a carga de trabalho administrativo dos servidores da saúde.

O projeto visa oferecer uma interface acessível via navegador em
que o usuário seleciona opções rápidas ou digita um termo e recebe dados do Código Internacional de Doenças ou localizações de farmácias onde o remédio é distribuído.


---

## Tecnologias empregadas

- **Python 3.11+** e **Django 6.0**: back‑end web MVC
- **pandas**: leitura e filtragem de arquivo CSV (`Medicamentos - unificado.csv`)
- **fuzzywuzzy**: comparação de strings para buscas semelhantes
- **JavaScript**: lógica do chat, chamadas ao backend,
  geração dinâmica de elementos, estilos e controle de estado
- **Leaflet**: exibição de mapa e marcadores
- **HTML/CSS**: layout responsivo (template `index.html` + `style.css`)

---

## Como executar

1. **Clone o repositório** e entre na pasta do projeto.

2. **Crie e ative** um ambiente virtual (venv/conda/etc.):

   ```sh
   python -m venv .venv
   source .venv/bin/activate    # Unix
   .venv\Scripts\activate       # Windows

3. **Instale as dependências**
    ```
    pip install -r requirements.txt
    

4. **Configure variáveis de ambiente**

    Crie um arquivo .env no diretório raiz com 
    ```
    SECRET_KEY=chave_secreta 
    ALLOWED_HOSTS="localhost,127.0.0.1"
    ```

5. Execute o servidor localmente

```
python manage.py runserver
```