# Docker Cheatsheet

## Containers

| Command                                                | What it does                            |
| ------------------------------------------------------ | --------------------------------------- |
| `docker run -d --name <name> -p 5432:5432 postgres:16` | Run a container in the background       |
| `docker ps`                                            | List running containers                 |
| `docker ps -a`                                         | List all containers (including stopped) |
| `docker stop <name>`                                   | Stop a container                        |
| `docker start <name>`                                  | Start a stopped container               |
| `docker restart <name>`                                | Restart a container                     |
| `docker rm <name>`                                     | Remove a stopped container              |
| `docker rm -f <name>`                                  | Force remove a running container        |
| `docker logs <name>`                                   | View container logs                     |
| `docker logs -f <name>`                                | Follow container logs live              |

## Exec into a Container

```bash
docker exec -it <name> bash          # open a bash shell
docker exec -it pg-local psql -U postgres -d analytics  # open psql directly
```

## Images

| Command                   | What it does                  |
| ------------------------- | ----------------------------- |
| `docker images`           | List local images             |
| `docker pull postgres:16` | Pull an image from Docker Hub |
| `docker rmi <image>`      | Remove an image               |

## Volumes & Ports

| Flag                            | What it does                   |
| ------------------------------- | ------------------------------ |
| `-p 5432:5432`                  | Map host port → container port |
| `-v /host/path:/container/path` | Bind mount a host directory    |
| `-v myvolume:/container/path`   | Use a named volume             |
| `docker volume ls`              | List named volumes             |
| `docker volume rm <name>`       | Remove a named volume          |

## Environment Variables

```bash
docker run -e POSTGRES_PASSWORD=password -e POSTGRES_USER=postgres postgres:16
```

## Cleanup

```bash
docker system prune          # remove stopped containers, dangling images, unused networks
docker system prune -a       # also remove unused images
docker volume prune          # remove unused volumes
```

## This Project

```bash
# Start the local Postgres container
docker start pg-local

# Connect to the analytics database
docker exec -it pg-local psql -U postgres -d analytics

# Stop when done
docker stop pg-local
```
