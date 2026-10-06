<img width="3410" height="1216" alt="Gemini_Generated_Image_usmwzqusmwzqusmw" src="https://github.com/user-attachments/assets/1289868a-ba01-457f-b93f-95d7ccfbdaa1" />

# CryptDrive
O CryptDrive é um chat por pen drive para uma troca segura de mensagens offline através de dispositivos de armazenamento USB. O sistema guarda a mensagem encriptada num pen drive, que pode ser lida num computador diferente, desde que tenha a mesma chave secreta.

## Funcionalidades

* Cadastro e autenticação de usários
* Interface gráfica para interação com o sistema
* Geração de estutura em árvore para mensagens
* Criptografar mensagens
* Descriptografia de mensagens recebinas
* Armazenamento das mensagens em dispositivo USB
* Histórico de Mensagens
* Comunicação offline entre computadores

## Como Executar

### 1. Pré-requisitos
Antes de começar, você vai precisar ter instalado em sua máquina as seguintes ferramentas:
* Python 3
* Git

### 2. Instalação e Execução

### Opção 1: Baixando o arquivo ZIP
* no topo da página do GitHub, clique no botão verde "Code" e escolha "Dowload ZIP"
* Extraia a pasta no seu computador 
* Abra no VS Code ou na IDE que você utiliza 
* Digite o comando para instalar a dependência: 'pip install cryptography'
* Clique no botão de "Play" para rodar o código


### Opção 2: Via git
Se você tem o Git instalado, basta abrir o terminal e executar os comandos abaixo linha por linha:

```bash
# 1. Clone o repositório
git clone https://github.com/vinicius607/Chat-Pen-Drive.git
```

```bash
# 3. Instale a biblioteca necessária
pip install cryptography
```
Depois de fazer isso, é só rodar o código.

## Manual de Uso
1. Cadastro e Login:
 * Ao abrir o aplicativo, digite um nome de usuário (entre 3 e 20 caracteres) e uma senha (mínimo de 4 caracteres) e clique em "Cadastrar". Depois, para fazer login, informe também uma Chave secreta do chat. Atenção: essa chave secreta precisa ser exatamente a mesma nos dois computadores que vão trocar mensagens.
  
2. Configuração do Pen Drive:
 * No canto superior direito da tela principal, clique em "Escolher pen drive" e selecione a unidade ou pasta do seu dispositivo USB.

3. Envio de Mensagens:
 * Na aba Escrever, digite sua mensagem no editor de texto.
 * Clique em "Gerar árvore". (Se a mensagem tiver até 1000 letras, você pode clicar em "Ver desenho da árvore" para conferir a estrutura gerada).
 * Clique em "Criptografar árvore" para aplicar a criptografia.
 * Clique em "Salvar no Pen Drive" para exportar o arquivo.

4. Leitura de Mensagens:
* Conecte o pendrive com as mensagens recebidas.
* Na aba Ler, clique em "Ler do Pen Drive".
* O sistema buscará arquivos .enc gerados por outros usuários, descriptografará o conteúdo e exibirá no histórico.

## Autores
* Vinicius Pimentel de Souza
* Felipe Alves de Pinho Cruz
* Gabriel luiz da silva custodio
* Matheus Rodrigues da Silva Neves
