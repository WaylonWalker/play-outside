default: build tag push convert set-image  deploy
fresh: create-ns cred convert deploy viz
update: convert patch

regcred:
    kubectl get secret -n default regcred --output=yaml -o yaml | sed 's/namespace: default/namespace: play-outside/' | kubectl apply -n play-outside -f - && echo deployed secret || echo secret exists
build:
    podman build -t docker.io/waylonwalker/play-outside -f Dockerfile .
tag:
    podman tag docker.io/waylonwalker/play-outside docker.io/waylonwalker/play-outside:$(hatch version)
push:
    podman push docker.io/waylonwalker/play-outside docker.io/waylonwalker/play-outside:$(hatch version)
    podman push docker.io/waylonwalker/play-outside docker.io/waylonwalker/play-outside:latest
set-image:
    kubectl set image deployment/play-outside-wayl-one --namespace play-outside play-outside-wayl-one=docker.io/waylonwalker/play-outside:$(hatch version)

create-ns:
    kubectl create ns play-outside && echo created ns play-outside || echo namespace play-outside already exists
cred:
    kubectl get secret regcred --output=yaml -o yaml | sed 's/namespace: default/namespace: play-outside/' | kubectl apply -n play-outside -f - && echo deployed secret || echo secret exists
convert:
    kompose convert -o deployment.yaml -n play-outside --replicas 3
deploy:
    kubectl apply -f deployment.yaml
delete:
    kubectl delete all --all -n play-outside --timeout=0s
viz:
    k8sviz -n play-outside --kubeconfig $KUBECONFIG -t png -o play-outside-k8s.png
restart:
    kubectl rollout restart -n play-outside deployment/play-outside-wayl-one
patch:
    kubectl patch -f deployment.yaml

describe:
    kubectl get deployment -n play-outside
    kubectl get rs -n play-outside
    kubectl get pod -n play-outside
    kubectl get svc -n play-outside
    kubectl get ing -n play-outside


describe-pod:
    kubectl describe pod -n play-outside

logs:
    kubectl logs --all-containers -l io.kompose.service=play-outside-wayl-one -n play-outside -f
