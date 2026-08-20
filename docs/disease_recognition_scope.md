CROPGUARD NETWORK — DISEASE RECOGNITION FEATURE ADDITIONS
=============================================================
Date: August 2026
Scope: Additions specific to the disease detection/recognition pipeline
(separate from market/shop/heatmap features covered in the main PRD)


WHY THESE ADDITIONS MATTER
-----------------------------
The baseline plan (YOLOv8 object detection across 5 crops) is already a meaningful step up
from typical student projects, most of which do whole-image classification only (see
comparison against Shubham-Jain-09/Crop-Disease-Detection: CNN + AlexNet, classification-
only, no localization, no severity, no evaluation metrics reported).

The additions below push the recognition pipeline from "detects and localizes disease"
to "detects, localizes, estimates severity, knows when it's unsure, and handles messy
real-world input" — a meaningfully more production-grade behavior set.


v1 FEATURES (BUILD THESE NOW)
================================

1. SEVERITY ESTIMATION
-------------------------
What: Instead of only outputting "disease X detected," estimate how much of the leaf/
plant is affected — Mild / Moderate / Severe — by calculating the ratio of infected
bounding-box area to total leaf area in the image.

Why it matters: Feeds directly into the RAG advisory response. A mild infection can
suggest "monitor and recheck in a few days," while a severe one can trigger an immediate
treatment recommendation. This makes the tool more useful, not just more technically
impressive.

Implementation notes:
  - Requires a rough leaf-area estimate per image (can be approximated via image
    segmentation or a simple leaf-boundary detection step before/alongside YOLOv8)
  - Store severity as a field alongside disease_detected and confidence_score in the
    disease_reports table (see main PRD Section 7.1)
  - Add severity as a queryable field for the advisory RAG assistant's context


2. MULTI-DISEASE DETECTION PER IMAGE
---------------------------------------
What: Since YOLOv8 is an object detector (not a single-label classifier), it can
naturally output multiple bounding boxes with different disease labels in the same
image, if more than one disease is present.

Why it matters: Real field photos often show co-occurring issues (e.g., a fungal
infection alongside pest damage). Most tutorial-style disease detectors assume one
disease per image, which doesn't reflect real conditions. Supporting multiple detections
per image is a realistic behavior most comparable projects skip entirely.

Implementation notes:
  - No major architecture change needed — this is largely about NOT collapsing
    multiple YOLOv8 detections down to a single "top" prediction in the API response
  - Update the API response schema to return a list of detections (each with its own
    disease label, bounding box, confidence, and severity) instead of a single object
  - Update the frontend DiagnosisResult component to display multiple detected issues
    if present


3. CONFIDENCE-BASED TRIAGE / UNCERTAINTY FLAGGING
-----------------------------------------------------
What: When YOLOv8's detection confidence falls below a defined threshold (e.g., 60%),
don't confidently state a diagnosis. Instead, flag the result as "Needs Review" and
route it differently (e.g., suggest the farmer retake the photo, or flag for extension
officer review).

Why it matters: This mirrors the critic/guardrail pattern already proven in the Guarded
Self-Critiquing RAG System — knowing when NOT to trust a model's own output is a real
production-ML competency, not just an accuracy number. Confidently wrong predictions
are worse than admitting uncertainty, especially when the output influences real
pesticide-use decisions.

Implementation notes:
  - Define confidence threshold per crop/disease class (may need tuning per class,
    since weaker datasets like Wheat may warrant a higher threshold)
  - Add a "needs_review" boolean/status field to disease_reports
  - Low-confidence results can optionally be queued for extension officer review
    (ties into the existing Extension Officer role from the auth scope decisions)


4. IMAGE QUALITY GATING (PRE-INFERENCE CHECK)
-------------------------------------------------
What: Before running YOLOv8 inference, run a lightweight quality check on the uploaded
image — blur detection (e.g., Laplacian variance method), basic brightness/exposure
check, and optionally a simple "is this actually a leaf/plant" sanity check.

Why it matters: Real farmer-submitted photos will be messy — blurry, poorly lit, wrong
subject entirely. Rejecting bad photos with a clear, actionable message ("Photo too
blurry, please retake in better light") is the difference between a lab demo and a
field-ready tool. This is a cheap, high-value addition.

Implementation notes:
  - Laplacian variance blur check: simple OpenCV operation, negligible compute cost
  - Add this as a pre-processing step in vision/preprocess.py, before the image reaches
    yolo_inference.py
  - Return a clear rejection reason in the API response so the frontend can show
    farmer-friendly guidance, not a generic error


UPDATED disease_reports SCHEMA (reflecting the above)
---------------------------------------------------------
Field                   Type        Notes
id                      UUID        Primary key
farmer_id               UUID        FK to farmers table
crop_type               VARCHAR     e.g., cotton, maize, wheat, soybean, sugarcane
detections              JSON/ARRAY  List of {disease, confidence, severity, bbox} —
                                    supports multi-disease detection (Feature 2)
needs_review            BOOLEAN     True if any detection is below confidence threshold
                                    (Feature 3)
image_quality_passed    BOOLEAN     False if rejected at pre-inference gating (Feature 4)
district                VARCHAR     Indexed for geospatial queries
lat, lng                FLOAT
image_url               VARCHAR     Azure Blob Storage reference
reported_at             TIMESTAMP


FUTURE SCOPE (NOT v1 — LATER PHASES)
=======================================

GRAD-CAM EXPLAINABILITY (Phase 2 candidate)
----------------------------------------------
What: Overlay a Grad-CAM heatmap on the analyzed image, showing which pixels/regions
the model actually used to make its prediction.

Why it matters: Builds farmer trust ("the model is looking at the actual infected
spot, not the background or an irrelevant part of the image") and is a genuine
technical differentiator — most student-level disease detection projects never touch
model explainability. Strong demo material for interviews and portfolio presentation.

Why it's Phase 2, not v1: Meaningfully more implementation effort than the four v1
features above — requires hooking into YOLOv8's intermediate layers, generating and
overlaying the heatmap, and validating that the highlighted regions are actually
meaningful (not just visually plausible). Worth doing once the core detection pipeline
across all 5 crops is stable and evaluated, not before.

Disease progression tracking over time (Phase 2/3 candidate)
------------------------------------------------------------
What: If a farmer photographs the same plant/field repeatedly, track how the infected
area/severity changes over time, turning single predictions into a monitoring timeline.
Requires a plant/field ID system not yet in v1 scope — deferred.

Few-shot / unknown-disease handling (Phase 3 candidate)
---------------------------------------------------------
What: When confidence is very low across ALL known disease classes (not just one),
flag the case as "possible unknown/unlisted disease" rather than forcing the nearest
known label. Prevents confidently wrong answers on genuinely novel cases. Deferred
until the core 5-crop model set is stable, since this needs reliable baseline confidence
calibration first.


SUMMARY
---------
v1 additions (build now): Severity Estimation, Multi-Disease Detection, Confidence-Based
Triage, Image Quality Gating — all moderate effort, all genuinely improve real-world
usefulness, not just benchmark numbers.

Future scope (documented, not built yet): Grad-CAM Explainability (Phase 2), Disease
Progression Tracking (Phase 2/3), Few-Shot Unknown-Disease Handling (Phase 3).
