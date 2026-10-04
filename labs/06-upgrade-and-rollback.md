# Lab 06 · Upgrade quotes-api to v2, then roll back

## Task

Release quotes-api `2.0.0` (it adds a field `served_by`: the Pod that answered), roll it out without downtime, then
roll back to `1.0.0`.

## Requirements

1. Build `quotes-api:2.0.0` from the same Dockerfile with `--build-arg APP_VERSION=2.0.0`, load it into kind.
2. Update the Deployment with `kubectl set image`, record a change cause, wait for the rollout.
3. Show the rollout history and the new field.
4. Roll back to the previous revision and prove that the answers have no `served_by` anymore.
5. Clean up everything the labs created.

## Hints

- The app adds `served_by` whenever its version is not `1.0.0` (read [app.py](quotes-api/app.py)).
- `kubectl annotate deployment/quotes-api kubernetes.io/change-cause="..."` fills the CHANGE-CAUSE column.

## Expected result

During 2.0.0: `"served_by": "quotes-api-..."` in the answer. After the undo: version `1.0.0`, no `served_by`.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: timeout=900; contains=successfully rolled out -->
```bash
docker build --build-arg APP_VERSION=2.0.0 -t quotes-api:2.0.0 labs/work/quotes-api > /dev/null
kind load docker-image quotes-api:2.0.0 --name bookshop > /dev/null
kubectl set image deployment/quotes-api quotes-api=quotes-api:2.0.0
kubectl annotate deployment/quotes-api kubernetes.io/change-cause="quotes-api 2.0.0: served_by" --overwrite > /dev/null
kubectl rollout status deployment/quotes-api --timeout=240s
```

<!-- test: retry=10; contains=served_by; contains=2.0.0; output -->
```bash
kubectl rollout history deployment/quotes-api
curl -s http://bookshop.localhost:8080/api/quotes; echo
```

```text
deployment.apps/quotes-api 
REVISION  CHANGE-CAUSE
1         <none>
2         quotes-api 2.0.0: served_by

{"quote": "Programs must be written for people to read.", "author": "Harold Abelson", "version": "2.0.0", "served_by": "quotes-api-664998546b-dlnhc"}
```

<!-- test: timeout=300; retry=10; contains="version": "1.0.0"; absent=served_by; output -->
```bash
kubectl rollout undo deployment/quotes-api > /dev/null
kubectl rollout status deployment/quotes-api --timeout=240s > /dev/null
curl -s http://bookshop.localhost:8080/api/quotes; echo
```

```text
Warning: resource deployments/quotes-api was previously managed with 'kubectl apply'. Rolling back will not update the kubectl.kubernetes.io/last-applied-configuration annotation, which may cause unexpected behavior on future 'kubectl apply' operations. Consider using 'kubectl apply' with your previous configuration file instead.
{"quote": "Make it work, make it right, make it fast.", "author": "Kent Beck", "version": "1.0.0"}
```

```text
⚠️ DESTRUCTIVE COMMAND · deletes quotes-api from the cluster and the lab's work folder.
```

<!-- test: timeout=300 -->
```bash
kubectl delete -f labs/work/k8s/quotes-api.yaml --ignore-not-found > /dev/null
rm -rf labs/work
```

</details>

## Explanation

The warning in the output is worth reading: `rollout undo` changed the live Deployment, but your YAML file still
says what you last applied. Keep the file the source of truth: after an emergency undo, fix the file and apply it.

The rollback did not rebuild anything: the Deployment kept the previous ReplicaSet (Pod template with
`quotes-api:1.0.0`) and scaled it up again. That works only because `1.0.0` is an immutable tag that still points
to exactly the image that ran before. With `latest`, "previous" would be whatever `latest` means today.

Back to the [labs](README.md), or on to the [capstone](../capstone/README.md).
