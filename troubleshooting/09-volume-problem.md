# 09 · Volume problem: a Pod stuck in Pending

> Time: 15 minutes. Uses the namespace `bookshop` of the [Kubernetes lessons](../kubernetes/README.md). The lab
> creates its own small Pod and volume claim and deletes them at the end; the platform is not touched.

## Break it

A new component needs a little persistent storage. Its manifest was copied from a cloud cluster that has a
StorageClass called `fast-ssd`:

<!-- test: contains=persistentvolumeclaim/scratch-data created; contains=pod/scratch-writer created -->
```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: scratch-data
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Mi
---
apiVersion: v1
kind: Pod
metadata:
  name: scratch-writer
spec:
  containers:
    - name: writer
      image: busybox:1.37
      command: ["sh", "-c", "date > /data/started && sleep 3600"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: scratch-data
EOF
```

## Problem

The Pod never starts. No logs, no crash, nothing.

## Symptoms

<!-- test: retry=10; contains=Pending; output -->
```bash
kubectl get pod scratch-writer
kubectl get pvc scratch-data
```

```text
NAME             READY   STATUS    RESTARTS   AGE
scratch-writer   0/1     Pending   0          1s
NAME           STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
scratch-data   Pending                                      fast-ssd       <unset>                 1s
```

## Investigation

`Pending` means the Pod has not been placed on a node yet, so there is nothing to log. The scheduler explains why in
the Pod's events; the claim has its own events.

## Commands

<!-- test: retry=15; contains=unbound; output -->
```bash
kubectl get events --field-selector involvedObject.name=scratch-writer | tail -2
```

```text
4m51s       Normal    Killing            pod/scratch-writer   Stopping container writer
1s          Warning   FailedScheduling   pod/scratch-writer   0/2 nodes are available: pod has unbound immediate PersistentVolumeClaims. not found
```

<!-- test: retry=15; contains=fast-ssd; output -->
```bash
kubectl describe pvc scratch-data | sed -n '/Events:/,$p'
kubectl get storageclass
```

```text
Events:
  Type     Reason              Age   From                         Message
  ----     ------              ----  ----                         -------
  Warning  ProvisioningFailed  1s    persistentvolume-controller  storageclass.storage.k8s.io "fast-ssd" not found
NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
standard (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  39m
```

## Root cause

The claim asks for the StorageClass `fast-ssd`, which does not exist in this cluster (kind has one class,
`standard`). Nothing can create a volume for the claim, the claim stays unbound, and a Pod that needs an unbound
claim cannot be scheduled.

## Fix

The StorageClass of a claim cannot be changed after it is created. Delete the Pod and the claim, then create them
again with the cluster's class (or leave `storageClassName` out to get the default class).

```text
⚠️ DESTRUCTIVE COMMAND · deletes the Pod scratch-writer and the claim scratch-data (empty: it never got a volume).
```

<!-- test: timeout=180; contains=deleted -->
```bash
kubectl delete pod scratch-writer --wait=true
kubectl delete pvc scratch-data
```

<!-- test: contains=created -->
```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: scratch-data
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: standard
  resources:
    requests:
      storage: 100Mi
---
apiVersion: v1
kind: Pod
metadata:
  name: scratch-writer
spec:
  containers:
    - name: writer
      image: busybox:1.37
      command: ["sh", "-c", "date > /data/started && sleep 3600"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: scratch-data
EOF
```

## Verification

<!-- test: timeout=300; retry=60; contains=Bound; contains=Running; output -->
```bash
kubectl get pod scratch-writer
kubectl get pvc scratch-data
```

```text
NAME             READY   STATUS    RESTARTS   AGE
scratch-writer   1/1     Running   0          4s
NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
scratch-data   Bound    pvc-6593a43b-c9b0-4271-b61f-08f8e17035a5   100Mi      RWO            standard       <unset>                 4s
```

<!-- test: retry=10; contains=UTC; output -->
```bash
kubectl exec scratch-writer -- cat /data/started
```

```text
Sun Oct  4 18:53:57 UTC 2026
```

The Pod runs and wrote to its volume. This was only a test component: remove it.

```text
⚠️ DESTRUCTIVE COMMAND · deletes the Pod scratch-writer and the claim scratch-data with its volume.
```

<!-- test: timeout=180; contains=deleted -->
```bash
kubectl delete pod scratch-writer --wait=true
kubectl delete pvc scratch-data
```

## Lesson learned

- `Pending` → `kubectl describe pod` / events: the scheduler always says why ("unbound PersistentVolumeClaims",
  "Insufficient memory", "untolerated taint", ...).
- StorageClass names are cluster-specific. `kubectl get storageclass` before you copy a manifest between clusters.
- Some fields of a claim are immutable: fixing them means recreating the claim (and losing what was in it).
