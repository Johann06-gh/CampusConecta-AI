# Despliegue en Oracle Cloud Infrastructure (OCI)

La opción recomendada para este proyecto es **OCI Container Instances** porque ejecuta directamente la imagen Docker sin administrar un servidor completo.

## 1. Preparar el repositorio de imágenes en OCIR

1. En OCI, abre **Developer Services → Containers & Artifacts → Container Registry**.
2. Crea un repositorio llamado `campusconecta-ai`.
3. Obtén estos valores:
   - `<region-key>`: por ejemplo `iad`, `gru` o el código de tu región.
   - `<tenancy-namespace>`: aparece en los detalles de la tenencia.
   - `<username>`: usuario de OCI.
   - `<auth-token>`: créalo desde el perfil del usuario en **Auth tokens**.

Inicia sesión en el registro:

```bash
docker login <region-key>.ocir.io
```

Cuando Docker solicite los datos:

```text
Usuario: <tenancy-namespace>/<username>
Contraseña: <auth-token>
```

## 2. Construir y subir la imagen

Desde la raíz del proyecto:

```bash
docker build -t campusconecta-ai:1.0 .
docker tag campusconecta-ai:1.0 <region-key>.ocir.io/<tenancy-namespace>/campusconecta-ai:1.0
docker push <region-key>.ocir.io/<tenancy-namespace>/campusconecta-ai:1.0
```

En equipos Apple Silicon o cuando OCI use arquitectura AMD64:

```bash
docker buildx build --platform linux/amd64 \
  -t <region-key>.ocir.io/<tenancy-namespace>/campusconecta-ai:1.0 \
  --push .
```

## 3. Crear la instancia de contenedor

1. Abre **Developer Services → Container Instances**.
2. Selecciona **Create container instance**.
3. Elige un nombre, compartment y shape disponible.
4. Usa una **subred pública** y asigna una **IPv4 pública**.
5. En el contenedor selecciona la imagen de OCIR subida anteriormente.
6. Configura estas variables de entorno:

```text
PORT=8080
DATA_PATH=data/servicios_estudiantiles.csv
GEMINI_API_KEY=<tu_clave_de_Gemini>
GEMINI_MODEL=gemini-2.5-flash
ALLOW_FALLBACK=true
```

7. Usa la política de reinicio **Always**.

## 4. Abrir el puerto de la aplicación

En la Security List o Network Security Group de la subred agrega una regla de ingreso:

```text
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination port: 8080
Description: CampusConecta AI web
```

Para producción real, restringe el origen o coloca un balanceador HTTPS delante del contenedor.

## 5. Probar la aplicación

Obtén la IPv4 pública de la instancia y abre:

```text
http://<IP_PUBLICA>:8080
```

Comprueba además:

```text
http://<IP_PUBLICA>:8080/api/health
http://<IP_PUBLICA>:8080/docs
```

## 6. Registrar la evidencia requerida

1. Copia el enlace público en la sección **Aplicación desplegada** del `README.md`.
2. Guarda una captura dentro de `docs/evidencias/oci-app.png`.
3. Actualiza el README con la imagen:

```markdown
![Aplicación ejecutándose en OCI](docs/evidencias/oci-app.png)
```

No publiques tu clave de Gemini, token de OCI ni archivo `.env`.
