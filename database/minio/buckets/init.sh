#!/bin/sh
# =====================================================
# MinIO Bucket Initialization Script
# Multi-Camera Person Tracking System
# =====================================================
# Runs as a one-shot Docker service after MinIO is healthy.
# Uses MinIO Client (mc) to create required buckets.
# =====================================================

set -e

MINIO_ENDPOINT="${MINIO_ENDPOINT:-minio:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin}"
MC_ALIAS="local"

echo "==> Waiting for MinIO to be ready at ${MINIO_ENDPOINT}..."
until mc alias set "${MC_ALIAS}" "http://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" > /dev/null 2>&1; do
    echo "  MinIO not ready yet. Retrying in 3s..."
    sleep 3
done
echo "==> MinIO is ready."

# ---- Create Buckets ----

create_bucket() {
    BUCKET=$1
    POLICY=$2
    if mc ls "${MC_ALIAS}/${BUCKET}" > /dev/null 2>&1; then
        echo "  Bucket '${BUCKET}' already exists. Skipping."
    else
        mc mb "${MC_ALIAS}/${BUCKET}"
        echo "  Bucket '${BUCKET}' created."
    fi

    if [ -n "${POLICY}" ]; then
        mc anonymous set "${POLICY}" "${MC_ALIAS}/${BUCKET}"
        echo "  Policy '${POLICY}' applied to '${BUCKET}'."
    fi
}

# person-crops: stores bounding-box crop images from AI pipeline (private)
create_bucket "person-crops" ""

# video-clips: stores short video clip excerpts (private)
create_bucket "video-clips" ""

# thumbnails: web-accessible thumbnails for dashboard (download-only)
create_bucket "thumbnails" "download"

echo "==> MinIO bucket initialization complete."

# ---- Lifecycle Policy: auto-expire crops older than 90 days ----
mc ilm import "${MC_ALIAS}/person-crops" << 'EOF'
{
    "Rules": [
        {
            "ID": "expire-old-crops",
            "Status": "Enabled",
            "Expiration": {
                "Days": 90
            }
        }
    ]
}
EOF
echo "==> Lifecycle policy applied to 'person-crops' (90-day auto-expiry)."
