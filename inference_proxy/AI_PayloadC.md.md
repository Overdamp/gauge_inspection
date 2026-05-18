# AI Payload (Version 8 - Revised)

  Luke

This version standardizes the inference result structure across all AI models

while keeping a consistent top-level envelope and allowing task-specific

payloads inside each `results[]` item.

This revision changes the `outputs` field from a key-value array structure into

a **flat object** structure for easier downstream consumption.

This revision also clarifies the separation between:

- **inference execution status** (`inference_status`, `inference_error`)

- **object-level condition** (`object_condition`)

- **AI outputs** (`outputs`, `ocr`, `normalized`)

- **user feedback / actual final result history** (`feedback[]`)

## Schema Overview

This version uses a **common envelope** for all inference tasks and allows

**task-specific result fields** inside each `results[]` item.

### 1. Common Envelope (recommended for all tasks)

The following top-level fields should remain consistent across all models:

- `inference_request_id`

- `timestamp`

- `image_uri`

- `inference_task`

- `results`

### 2. Object / Event / Measurement Tasks

Tasks such as:

- `digital_gauge_reading`

- `analog_gauge_reading`

- `abnormality_detection`

- `water_level_estimation`

- `gas_detection`

- `scanning_devices`

should keep the same result-level conventions, while choosing the reference key

and payload fields that best match the task:

Use **`detection_id`** when the result is tied to a detected object in the

image, for example:

- digital gauge

- analog gauge

- abnormality detection on a detected object

- scanning devices

Use **`result_id`** when the result is scene-level, event-level, or otherwise

not tied to a single detected object, for example:

- gas detection over an area

- water-level estimation from a full sump view

- OCR-only cropped input

Typical fields for these tasks include:

- `detection_id` or `result_id`

- `inference_status`

- `inference_error`

- `object_type`

- `object_condition`

- `primary_detection` (if applicable)

- `components` (if applicable)

- `ocr` (if applicable)

- `outputs` (if applicable)

- `feedback` (optional, array of review history records scoped to this

  `detection_id` or `result_id`)

- `debug`

### 3. OCR-Only or User-Cropped Tasks

Tasks such as:

- `ocr_text_extraction`

- `nameplate_text_extraction`

- `equipment_tag_ocr`

may **omit detection-specific fields** when object detection is not part of the

pipeline.

Recommended fields for OCR-only tasks:

- `result_id`

- `inference_status`

- `inference_error`

- `object_type`

- `source_region`

- `ocr`

- `normalized`

- `debug`

## Common Response Schema

```jsonc

{

  "inference_request_id": "0daf3458-5cb1-5494-94aa-b2bd0c4a20f9",

  "timestamp": "2026-03-26T19:20:05.112+07:00",

  "image_uri": "s3://robot-1:9090/snapshots/e29963cc-3661-4646-8f7c-a4a149f9464b.png",

  "inference_task": 0,

  "results": [

    {

      "detection_id": 1,

      "inference_status": "SUCCESS", // SUCCESS | PARTIAL | FAILED

      "inference_error": null,

      "object_type": "digital_gauge",

      "object_condition": "NORMAL", // NORMAL | ABNORMAL | null

      "primary_detection": {

        "class_name": "digital_gauge",

        "class_id": 0,

        "confidence": 0.95,

        "bbox": [

          200,

          250,

          400,

          450

        ]

      },

      "components": {},

      "ocr": [],

      "outputs": {},

      "feedback": [],

      "debug": null

    }

  ]

}

```

### Notes

- The example above shows a **detection-based task**.

- For OCR-only tasks, the top-level envelope should remain the same, but each

  `results[]` item may use `result_id` and `source_region` instead of

  `detection_id` and `primary_detection`.

- `object_condition` is an object-level interpretation and should appear near

  `object_type` for quick reading.

- `feedback` is reserved for user review history and actual final result

  capture. It should be stored as an array inside each `results[]` item and must

  not overwrite AI-generated values.

- `outputs` is now a **flat object** (not a key-value array). Use `{}` when

  there are no outputs.

### `prediction_result` values

- `correct` → AI ถูกต้อง

- `over_detected` → AI บอกผิดปกติ แต่จริงๆ ปกติ

- `under_detected` → AI บอกปกติ แต่จริงๆ ผิดปกติ

- `misclassified` → detect เจอ แต่ประเภท/ค่า/unit ผิด

## Common Data Dictionary

### 1. Metadata

| Field | Description |

| :--- | :--- |

| **`inference_request_id`** | Unique identifier for this inference request. |

| **`timestamp`** | Timestamp of inference result generation in ISO-8601 format. |

| **`image_uri`** | URI/URL of the image used for AI processing. |

| **`inference_task`** | Numeric identifier of the AI task, e.g. `0`. |

| **`results`** | Array of inference results. One item corresponds to one detected object or one OCR result item, depending on the task. |

### 2. Core Result Fields

| Field | Description |

| :--- | :--- |

| **`inference_status`** | Inference pipeline execution status for this result item: `SUCCESS`, `PARTIAL`, or `FAILED`. |

| **`inference_error`** | Error object if inference failed or was partial; otherwise `null`. |

| **`object_type`** | Normalized object type used consistently across the system, e.g. `digital_gauge`, `analog_gauge`, `flange`, `nameplate`. |

| **`object_condition`** | Object-level interpretation such as `NORMAL`, `ABNORMAL`, or `null` when the task cannot determine a condition. |

| **`debug`** | Optional model-specific debug information. |

### 3. Detection-Based Result Fields

| Field | Description |

| :--- | :--- |

| **`detection_id`** | Stable detected-object reference ID within the image. |

| **`primary_detection`** | Main detection result for the object. |

| **`components`** | Nested sub-components detected inside the object. |

| **`ocr`** | OCR results associated with one or more components. |

| **`outputs`** | AI task outputs for the object, represented as a **flat object** with task-specific keys. Covers gauge readings, abnormality types, severity, gas events, water levels, and other task-specific values. Use `{}` when there are no outputs. |

| **`feedback`** | Optional array of human review / actual final result records scoped to this `detection_id` or `result_id`. Use `[]` if not reviewed. |

### 4. OCR-Only Result Fields

| Field | Description |

| :--- | :--- |

| **`result_id`** | Stable result reference ID when no object detection step exists. |

| **`source_region`** | Information about the cropped input region, including whether the crop was provided by the user. |

| **`ocr`** | OCR output for the cropped region, either as a single object or a list depending on task design. |

| **`normalized`** | Optional normalized or parsed values derived from OCR text, e.g. `equipment_tag`. |

### 5. Inference Error

| Field | Description | Example |

| :--- | :--- | :--- |

| **`code`** | Machine-readable error code. | `OBSTRUCTION_DETECTED` |

| **`message`** | Human-readable error message. | `Gauge display is partially covered` |

| **`stage`** | Processing stage where the error happened. | `ocr`, `component_detection` |

Example:

```json

{

  "code": "DISPLAY_NOT_FOUND",

  "message": "Display region could not be localized",

  "stage": "component_detection"

}

```

### 6. Bounding Box (`bbox`)

The coordinates defining the rectangle around a detected object or component,

based on pixel coordinates:

```json

[x_min, y_min, x_max, y_max]

```

### 7. Polygon Mask (`mask`)

Polygon coordinates used for segmentation output:

```json

[

  [x, y],

  [x, y],

  [x, y],

  ...

]

```

### 8. Inference Status vs Object Condition

- **`inference_status`** describes whether the inference pipeline succeeded.

- **`object_condition`** describes the interpreted state of the object, such as

  `NORMAL` or `ABNORMAL`.

- **`outputs`** carries all AI task outputs as a flat object, including gauge

  readings, threshold levels, abnormality types, severity, and other

  task-specific values.

- OCR-only tasks may not use `object_condition` at all if the task output is

  only extracted text.

Examples:

- `inference_status = "FAILED"` means the object could not be processed

  correctly.

- `inference_status = "SUCCESS"` and `object_condition = "NORMAL"` means the

  object was processed correctly and no abnormality was found.

- `inference_status = "SUCCESS"` and `object_condition = "ABNORMAL"` means the

  object was processed correctly and one or more abnormalities were found.

- `inference_status = "SUCCESS"` and `outputs.gauge_level = "Normal"` means the

  gauge reading was extracted successfully and interpreted as normal.

### 9. Feedback

`feedback` is optional and is intended for **human review**, **actual final

result capture**, and **review history** for result items that need operator

confirmation.

Use `feedback` as an **array of append-only review records** inside each

`results[]` item. This allows multiple feedback submissions over time for the

same detected object or scene-level result and enables the system to show

historical review changes. If there is no feedback yet, use `feedback: []`.

**Feedback scope:**

- For detection-based tasks, each `results[].detection_id` owns its own

  `feedback[]` history.

- For scene-level, event-level, or OCR-only tasks without object detection, each

  `results[].result_id` owns its own `feedback[]` history if feedback is needed.

- `feedback_id` UUID V7.

- To uniquely reference one feedback record in a database, use a composite key

  such as `inference_request_id + detection_id + feedback_id`, or

  `inspection_id + detection_id + feedback_id` when an `inspection_id` exists.

  For `result_id`-based results, replace `detection_id` with `result_id`.

- Do not create a separate top-level `feedback` array for all detections,

  because that makes it easier to mismatch feedback with the wrong object in

  images that contain many detections.

Recommended structure inside each `results[]` item:

```jsonc

{

  "detection_id": 1,

  "object_type": "control_valve",

  "object_condition": "ABNORMAL",

  "outputs": {

    "abnormality_type": "oil_leak",

    "severity": "low",

    "confidence": 0.78

  },

  "feedback": [

    {

      "feedback_id": 1,

      "prediction_result": "correct", // correct | over_detected | under_detected | misclassified

      "review_state": "CONFIRMED_CASE", // CONFIRMED_CASE | REMEDIATED_CASE | DISMISSED_CASE | NORMAL_CASE

      "reviewed_by": "operator_01",

      "reviewed_at": "2026-04-09T15:10:00+07:00",

      "comment": "Operator verified the final result for this detection",

      "actual_object_condition": "ABNORMAL", // NORMAL | ABNORMAL | null

      "actual_measurement": null,

      "actual_outputs": {

        "abnormality_type": "oil_leak",

        "severity": "medium"

      }

    }

  ]

}

```

#### Multiple Feedback History Example for One Detection

```jsonc

{

  "detection_id": 2,

  "object_type": "control_valve",

  "object_condition": "ABNORMAL",

  "outputs": {

    "abnormality_type": "oil_leak",

    "severity": null,

    "confidence": 0.62

  },

  "feedback": [

    {

      "feedback_id": 1, // UUID v7

      "prediction_result": "over_detected",

      "review_state": "DISMISSED_CASE",

      "reviewed_by": "operator_01",

      "reviewed_at": "2026-04-09T15:10:00+07:00",

      "comment": "Initial review dismissed the alarm after checking the image",

      "actual_object_condition": "NORMAL",

      "actual_measurement": null,

      "actual_outputs": {}

    },

    {

      "feedback_id": 2, // UUID v7

      "prediction_result": "correct",

      "review_state": "CONFIRMED_CASE",

      "reviewed_by": "supervisor_01",

      "reviewed_at": "2026-04-09T16:30:00+07:00",

      "comment": "Supervisor rechecked on site and confirmed the abnormality",

      "actual_object_condition": "ABNORMAL",

      "actual_measurement": null,

      "actual_outputs": {

        "abnormality_type": "oil_leak",

        "severity": "medium"

      }

    }

  ]

}

```

#### Feedback Field Definitions

| Field | Description |

| :--- | :--- |

| **`feedback[]`** | Array of human review records. Use `[]` when no feedback has been submitted. |

| **`feedback[].feedback_id`** | Numeric identifier for this feedback record. Start from `1` and increment within the same `results[]` item. It may restart for each different `detection_id` or `result_id`. |

| **`feedback[].prediction_result`** | Human judgment of the AI prediction: `correct`, `over_detected`, `under_detected`, or `misclassified`. |

| **`feedback[].review_state`** | Human review state for this feedback record. |

| **`feedback[].reviewed_by`** | User, operator, or reviewer identifier. |

| **`feedback[].reviewed_at`** | Review timestamp in ISO-8601 format. |

| **`feedback[].comment`** | Free-text explanation or review note. |

| **`feedback[].actual_object_condition`** | Human-confirmed final object condition, usually `NORMAL`, `ABNORMAL`, or `null`. |

| **`feedback[].actual_measurement`** | Human-confirmed final gauge reading, water level, or other structured numeric result. |

| **`feedback[].actual_outputs`** | Human-confirmed final task outputs as a flat object. Mirrors the structure of `outputs`. Use `{}` when reviewer confirms normal or dismisses the case. |

#### Recommended Prediction Result Meanings

| Value | Meaning |

| :--- | :--- |

| **`correct`** | AI output matches the human-confirmed result. |

| **`over_detected`** | AI reported an abnormality, alarm, or non-normal condition, but the reviewer confirms it should not be treated as a real case. |

| **`under_detected`** | AI missed an abnormality, alarm, or non-normal condition that the reviewer confirms exists. |

| **`misclassified`** | AI detected the object but the predicted type, value, or unit is wrong (e.g. wrong abnormality type, wrong gauge reading, wrong unit, wrong severity). |

#### Recommended Review State Meanings

| Value | Meaning |

| :--- | :--- |

| **`CONFIRMED_CASE`** | The reviewer confirms the case or final result as valid. |

| **`REMEDIATED_CASE`** | The case was valid but has already been remediated. |

| **`DISMISSED_CASE`** | The case is dismissed, for example as an over-detected or non-actionable case. |

| **`NORMAL_CASE`** | The reviewer confirms the object is normal and there is no abnormality case. |

Design rules:

1. `feedback` should not overwrite AI-generated fields such as `outputs`.

2. `feedback` belongs to the specific `results[]` item where it appears. For

   detection-based tasks, this means the feedback is tied to that exact

   `detection_id`.

3. `feedback` should be append-only. Do not edit or delete older feedback

   records; add a new record with the next numeric `feedback_id` within the same

   `detection_id` or `result_id`.

4. The latest feedback record should normally be selected by the latest

   `reviewed_at`; if timestamps are equal or unavailable, use the highest

   numeric `feedback_id` within that same result item.

5. For **gauge reading or water-level correction**, populate

   `actual_measurement` and optionally `actual_object_condition`.

6. For **abnormality or gas-event correction**, populate

   `actual_object_condition` and `actual_outputs`.

7. If a reviewer has not reviewed the result, use `feedback: []`.

8. `NORMAL_CASE` should usually pair with `actual_object_condition = "NORMAL"`

   and `actual_outputs = {}`.

9. `REMEDIATED_CASE` should be used when the case existed but has already been

   resolved by operation or maintenance.

## A. Digital Gauge

```jsonc

{

  "inference_request_id": "0daf3458-5cb1-5494-94aa-b2bd0c4a20f9",

  "timestamp": "2026-03-26T19:20:05.112+07:00",

  "image_uri": "s3://robot-1:9090/snapshots/e29963cc-3661-4646-8f7c-a4a149f9464b.png",

  "inference_task": 0,

  "results": [

    {

      "detection_id": 1,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "digital_gauge",

      "object_condition": "NORMAL",

      "primary_detection": {

        "class_name": "digital_gauge",

        "class_id": 0,

        "confidence": 0.95,

        "bbox": [

          515,

          115,

          635,

          235

        ]

      },

      "components": {

        "display_screen": {

          "component_id": "display_1",

          "confidence": 0.94,

          "bbox": [

            520,

            150,

            630,

            200

          ],

          "mask": null

        }

      },

      "ocr": [

        {

          "component_id": "display_1",

          "text": "120.5 psi",

          "confidence": 0.98,

          "center": null

        }

      ],

      "outputs": {

        "gauge_reading": 45.2,

        "unit": "psi",

        "confidence": 0.92,

        "gauge_level": "Normal"

      },

      "feedback": [],

      "debug": null

    },

    {

      "detection_id": 2,

      "inference_status": "FAILED",

      "inference_error": {

        "code": "OBSTRUCTION_DETECTED",

        "message": "Gauge display is partially covered",

        "stage": "ocr"

      },

      "object_type": "digital_gauge",

      "object_condition": null,

      "primary_detection": {

        "class_name": "digital_gauge",

        "class_id": 0,

        "confidence": 0.92,

        "bbox": [

          100,

          50,

          250,

          200

        ]

      },

      "components": {

        "display_screen": null

      },

      "ocr": [],

      "outputs": {},

      "feedback": [],

      "debug": null

    }

  ]

}

```

### Data Dictionary

| Field | Description | Example |

| :--- | :--- | :--- |

| **`results[].detection_id`** | Object reference ID for the gauge. | `1` |

| **`results[].inference_status`** | Inference pipeline execution status. | `"SUCCESS"`, `"FAILED"` |

| **`results[].inference_error`** | Error information if inference fails. | `{ "code": "OBSTRUCTION_DETECTED" }` |

| **`results[].object_condition`** | Object-level condition for the gauge result. | `"NORMAL"` |

| **`results[].primary_detection`** | Primary detection box and confidence of the gauge. | `{ "bbox": [515, 115, 635, 235] }` |

| **`results[].components.display_screen`** | Display region detected inside the gauge. | `{ "bbox": [520, 150, 630, 200] }` |

| **`results[].ocr[]`** | OCR text extracted from the display. | `"120.5 psi"` |

| **`results[].outputs`** | AI task outputs for the gauge result, as a flat object. | See output keys below. |

| **`results[].outputs.gauge_reading`** | Numeric reading value extracted from the display. | `120.5` |

| **`results[].outputs.unit`** | Unit extracted from the display. | `"psi"` |

| **`results[].outputs.confidence`** | Confidence score for the gauge reading. | `0.92` |

| **`results[].outputs.gauge_level`** | Operational threshold interpretation of the reading. Allowed values: `High`, `Normal`, `Low`. | `"Normal"` |

| **`results[].feedback`** | Optional review history array for actual final measurement. | `[]` |

### Feedback Example (Actual Gauge Value)

```json

{

  "detection_id": 1,

  "inference_status": "SUCCESS",

  "inference_error": null,

  "object_type": "digital_gauge",

  "object_condition": "NORMAL",

  "outputs": {

    "gauge_reading": 120.5,

    "unit": "psi",

    "confidence": 0.98,

    "gauge_level": "Normal"

  },

  "feedback": [

    {

      "feedback_id": 1,

      "prediction_result": "correct",

      "review_state": "CONFIRMED_CASE",

      "reviewed_by": "operator_01",

      "reviewed_at": "2026-04-09T15:10:00+07:00",

      "comment": "Operator verified final gauge reading from panel display",

      "actual_object_condition": "NORMAL",

      "actual_outputs": {

        "gauge_reading": 120.5,

        "unit": "psi",

        "gauge_level": "Normal"

      }

    }

  ]

}

```

### Failed Case Example

```json

{

  "detection_id": 3,

  "inference_status": "FAILED",

  "inference_error": {

    "code": "DISPLAY_NOT_FOUND",

    "message": "Display region could not be localized",

    "stage": "component_detection"

  },

  "object_type": "digital_gauge",

  "object_condition": null,

  "primary_detection": {

    "class_name": "digital_gauge",

    "class_id": 0,

    "confidence": 0.91,

    "bbox": [

      410,

      140,

      560,

      290

    ]

  },

  "components": {

    "display_screen": null

  },

  "ocr": [],

  "outputs": {},

  "feedback": [],

  "debug": null

}

```

## B. Analog Gauge

```jsonc

{

  "inference_request_id": "7d7ac2b1-d8b3-43cb-b2d5-114988c60122",

  "timestamp": "2026-03-26T19:20:05.112+07:00",

  "image_uri": "s3://robot-1:9090/snapshots/e29963cc-3661-4646-8f7c-a4a149f9464b.png",

  "inference_task": 1,

  "results": [

    {

      "detection_id": 1,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "analog_gauge",

      "object_condition": "NORMAL",

      "primary_detection": {

        "class_name": "analog-gauge",

        "class_id": 1,

        "confidence": 0.89,

        "bbox": [

          500,

          100,

          650,

          250

        ]

      },

      "components": {

        "gauge_body": {

          "component_id": "gauge_1",

          "confidence": 0.98,

          "bbox": [

            510,

            110,

            640,

            240

          ],

          "mask": [

            [

              510,

              110

            ],

            [

              640,

              110

            ],

            [

              640,

              240

            ],

            [

              510,

              240

            ]

          ]

        },

        "center": {

          "component_id": "centre_1",

          "confidence": 0.92,

          "bbox": [

            570,

            170,

            580,

            180

          ],

          "mask": [

            [

              570,

              170

            ],

            [

              580,

              170

            ],

            [

              580,

              180

            ],

            [

              570,

              180

            ]

          ]

        },

        "needle": {

          "component_id": "needle_1",

          "confidence": 0.94,

          "bbox": [

            530,

            140,

            575,

            175

          ],

          "mask": [

            [

              530,

              140

            ],

            [

              540,

              145

            ],

            [

              575,

              175

            ],

            [

              535,

              135

            ]

          ]

        },

        "scale_region": {

          "component_id": "scale_1",

          "confidence": 0.91,

          "bbox": [

            515,

            115,

            635,

            235

          ],

          "mask": [

            [

              515,

              115

            ],

            [

              635,

              115

            ],

            [

              635,

              235

            ],

            [

              515,

              235

            ]

          ]

        },

        "min_value_region": {

          "component_id": "min_val_1",

          "confidence": 0.96,

          "bbox": [

            520,

            180,

            535,

            195

          ],

          "mask": [

            [

              520,

              180

            ],

            [

              535,

              180

            ],

            [

              535,

              195

            ],

            [

              520,

              195

            ]

          ]

        },

        "max_value_region": {

          "component_id": "max_val_1",

          "confidence": 0.95,

          "bbox": [

            615,

            180,

            630,

            195

          ],

          "mask": [

            [

              615,

              180

            ],

            [

              630,

              180

            ],

            [

              630,

              195

            ],

            [

              615,

              195

            ]

          ]

        },

        "scale_number_regions": [

          {

            "component_id": "scale_num_1",

            "confidence": 0.92,

            "bbox": [

              540,

              120,

              555,

              135

            ],

            "mask": [

              [

                540,

                120

              ],

              [

                555,

                120

              ],

              [

                555,

                135

              ],

              [

                540,

                135

              ]

            ]

          },

          {

            "component_id": "scale_num_2",

            "confidence": 0.89,

            "bbox": [

              580,

              115,

              595,

              130

            ],

            "mask": [

              [

                580,

                115

              ],

              [

                595,

                115

              ],

              [

                595,

                130

              ],

              [

                580,

                130

              ]

            ]

          }

        ],

        "unit_region": {

          "component_id": "unit_1",

          "confidence": 0.97,

          "bbox": [

            565,

            200,

            585,

            215

          ],

          "mask": [

            [

              565,

              200

            ],

            [

              585,

              200

            ],

            [

              585,

              215

            ],

            [

              565,

              215

            ]

          ]

        }

      },

      "ocr": [

        {

          "component_id": "min_val_1",

          "text": "0",

          "confidence": 0.98,

          "center": [

            527,

            187

          ]

        },

        {

          "component_id": "max_val_1",

          "text": "100",

          "confidence": 0.97,

          "center": [

            622,

            187

          ]

        },

        {

          "component_id": "scale_num_1",

          "text": "25",

          "confidence": 0.95,

          "center": [

            547,

            127

          ]

        },

        {

          "component_id": "scale_num_2",

          "text": "50",

          "confidence": 0.93,

          "center": [

            587,

            122

          ]

        },

        {

          "component_id": "unit_1",

          "text": "bar",

          "confidence": 0.99,

          "center": [

            575,

            207

          ]

        }

      ],

      "outputs": {

        "gauge_reading": "45.2",

        "unit": "bar",

        "confidence": 0.92,

        "gauge_level": "normal"

      },

      "feedback": [],

      "debug": {

        "min_found": 0.0,

        "max_found": 100.0,

        "fit_points": 4,

        "total_points_detected": 5,

        "slope": 1.25,

        "needle_tip": [

          580,

          180

        ],

        "r2_score": 0.9856,

        "debug_cleaned_data": [

          [

            0.0,

            45.0

          ],

          [

            50.0,

            135.0

          ],

          [

            100.0,

            225.0

          ]

        ]

      }

    }

  ]

}

```

### Data Dictionary

| Field | Description | Example |

| :--- | :--- | :--- |

| **`results[].primary_detection`** | Main analog gauge bounding box. | `[500, 100, 650, 250]` |

| **`results[].components`** | Segmented sub-components of the gauge. | `needle`, `center`, `scale_region` |

| **`results[].ocr[]`** | OCR values extracted from text-bearing components. | `"100"`, `"bar"` |

| **`results[].outputs`** | AI task outputs for the gauge result, as a flat object. | See output keys below. |

| **`results[].outputs.gauge_reading`** | Final calculated analog reading. | `"45.2"` |

| **`results[].outputs.unit`** | Unit read from OCR. | `"bar"` |

| **`results[].outputs.confidence`** | Confidence score for the gauge reading. | `0.92` |

| **`results[].outputs.gauge_level`** | Operational threshold interpretation of the reading. Allowed values: `high`, `normal`, `low`. | `"normal"` |

| **`results[].feedback`** | Optional review history array for actual final value. | `[]` |

| **`results[].debug`** | Debug information for plotting and regression tracing, including `r2_score`. | `{ "needle_tip": [580, 180], "r2_score": 0.9856 }` |

### Failed Case Example

```json

{

  "detection_id": 1,

  "inference_status": "FAILED",

  "inference_error": {

    "code": "NEEDLE_NOT_DETECTED",

    "message": "Needle could not be localized for reading calculation",

    "stage": "component_detection"

  },

  "object_type": "analog_gauge",

  "object_condition": null,

  "primary_detection": {

    "class_name": "analog-gauge",

    "class_id": 1,

    "confidence": 0.90,

    "bbox": [

      120,

      80,

      300,

      260

    ]

  },

  "components": {

    "gauge_body": {

      "component_id": "gauge_2",

      "confidence": 0.95,

      "bbox": [

        125,

        85,

        295,

        255

      ],

      "mask": [

        [

          125,

          85

        ],

        [

          295,

          85

        ],

        [

          295,

          255

        ],

        [

          125,

          255

        ]

      ]

    },

    "center": null,

    "needle": null,

    "scale_region": null,

    "min_value_region": null,

    "max_value_region": null,

    "scale_number_regions": [],

    "unit_region": null

  },

  "ocr": [],

  "outputs": {},

  "feedback": [],

  "debug": null

}

```

## C. Abnormality Detection

```jsonc

{

  "inference_request_id": "4f420766-9ed0-43a9-9ad6-21d6eaa83fe9",

  "timestamp": "2026-03-26T19:20:05.112+07:00",

  "image_uri": "s3://robot-1:9090/snapshots/e29963cc-3661-4646-8f7c-a4a149f9464b.png",

  "inference_task": 2,

  "results": [

    {

      "detection_id": 1,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "flange",

      "object_condition": "ABNORMAL",

      "primary_detection": {

        "class_name": "Flange",

        "class_id": 0,

        "confidence": 0.92,

        "bbox": [

          300,

          400,

          450,

          550

        ]

      },

      "components": {},

      "ocr": [],

      "outputs": {

        "abnormality_type": "corrosion",

        "severity": 4,

        "confidence": 0.78

      },

      "feedback": [],

      "debug": null

    },

    {

      "detection_id": 2,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "control_valve",

      "object_condition": "ABNORMAL",

      "primary_detection": {

        "class_name": "Control_valve",

        "class_id": 1,

        "confidence": 0.88,

        "bbox": [

          100,

          800,

          350,

          950

        ]

      },

      "components": {},

      "ocr": [],

      "outputs": {

        "abnormality_type": "oil_leak",

        "severity": "LOW",

        "confidence": 0.78

      },

      "feedback": [],

      "debug": null

    }

  ]

}

```

### Data Dictionary

| Field | Description | Example |

| :--- | :--- | :--- |

| **`results[].object_type`** | Equipment or object type being inspected. | `flange`, `control_valve` |

| **`results[].object_condition`** | Object-level abnormality conclusion. | `"NORMAL"`, `"ABNORMAL"` |

| **`results[].primary_detection`** | Primary detection result of the inspected object. | `{ "bbox": [300, 400, 450, 550] }` |

| **`results[].outputs`** | AI abnormality outputs for the object as a flat object. Use `{}` when no abnormality is found. | See output keys below. |

| **`results[].outputs.abnormality_type`** | Detected abnormality type. | `"oil_leak"`, `"corrosion"` |

| **`results[].outputs.severity`** | Severity level of the detected abnormality. | `"LOW"`, `"MEDIUM"`, `"HIGH"`, or numeric scale (e.g. `4`) |

| **`results[].outputs.confidence`** | Confidence score for the abnormality finding. | `0.78` |

| **`results[].feedback`** | Optional review history array for corrected abnormality outcome. | `[]` |

### Multiple Detection Feedback History Example

When one image contains many detected objects, each object should remain as a

separate `results[]` item, and each item should keep its own `feedback[]`

history. `feedback_id` can restart from `1` for each `detection_id` because the

feedback is scoped to that result item.

```jsonc

{

  "inference_request_id": "4f420766-9ed0-43a9-9ad6-21d6eaa83fe9",

  "timestamp": "2026-03-26T19:20:05.112+07:00",

  "image_uri": "s3://robot-1:9090/snapshots/e29963cc-3661-4646-8f7c-a4a149f9464b.png",

  "inference_task": 2,

  "results": [

    {

      "detection_id": 1,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "flange",

      "object_condition": "ABNORMAL",

      "primary_detection": {

        "class_name": "Flange",

        "class_id": 0,

        "confidence": 0.92,

        "bbox": [

          300,

          400,

          450,

          550

        ]

      },

      "components": {},

      "ocr": [],

      "outputs": {

        "abnormality_type": "corrosion",

        "severity": "LOW",

        "confidence": 0.78

      },

      "feedback": [

        {

          "feedback_id": 1,

          "prediction_result": "misclassified",

          "review_state": "CONFIRMED_CASE",

          "reviewed_by": "inspector_01",

          "reviewed_at": "2026-04-09T15:10:00+07:00",

          "comment": "Corrosion confirmed on flange but severity should be MEDIUM",

          "actual_object_condition": "ABNORMAL",

          "actual_outputs": {

            "abnormality_type": "corrosion",

            "severity": "MEDIUM"

          }

        },

        {

          "feedback_id": 2,

          "prediction_result": "correct",

          "review_state": "REMEDIATED_CASE",

          "reviewed_by": "maintenance_01",

          "reviewed_at": "2026-04-10T09:30:00+07:00",

          "comment": "Corrosion cleaned and coating repaired",

          "actual_object_condition": "NORMAL",

          "actual_outputs": {}

        }

      ],

      "debug": null

    },

    {

      "detection_id": 2,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "control_valve",

      "object_condition": "ABNORMAL",

      "primary_detection": {

        "class_name": "Control_valve",

        "class_id": 1,

        "confidence": 0.88,

        "bbox": [

          100,

          800,

          350,

          950

        ]

      },

      "components": {},

      "ocr": [],

      "outputs": {

        "abnormality_type": "oil_leak",

        "severity": "LOW",

        "confidence": 0.78

      },

      "feedback": [

        {

          "feedback_id": 1,

          "prediction_result": "over_detected",

          "review_state": "DISMISSED_CASE",

          "reviewed_by": "inspector_02",

          "reviewed_at": "2026-04-09T15:20:00+07:00",

          "comment": "Stain on valve body, not active oil leak",

          "actual_object_condition": "NORMAL",

          "actual_outputs": {}

        }

      ],

      "debug": null

    }

  ]

}

```

### Normal Case Example

If no abnormality is found but the object is processed successfully:

```json

{

  "detection_id": 1,

  "inference_status": "SUCCESS",

  "inference_error": null,

  "object_type": "pipe",

  "object_condition": "NORMAL",

  "primary_detection": {

    "class_name": "Pipe",

    "class_id": 2,

    "confidence": 0.90,

    "bbox": [

      50,

      200,

      300,

      260

    ]

  },

  "components": {},

  "ocr": [],

  "outputs": {},

  "feedback": [],

  "debug": null

}

```

### Feedback Example (Confirmed Case)

```json

{

  "detection_id": 2,

  "inference_status": "SUCCESS",

  "inference_error": null,

  "object_type": "control_valve",

  "object_condition": "ABNORMAL",

  "outputs": {

    "abnormality_type": "oil_leak",

    "severity": "LOW",

    "confidence": 0.78

  },

  "feedback": [

    {

      "feedback_id": 1,

      "prediction_result": "misclassified",

      "review_state": "CONFIRMED_CASE",

      "reviewed_by": "inspector_02",

      "reviewed_at": "2026-04-09T15:15:00+07:00",

      "comment": "Leak confirmed on site but severity should be MEDIUM",

      "actual_object_condition": "ABNORMAL",

      "actual_measurement": null,

      "actual_outputs": {

        "abnormality_type": "oil_leak",

        "severity": "MEDIUM"

      }

    }

  ]

}

```

### Feedback Example (Normal Case)

```json

{

  "detection_id": 1,

  "inference_status": "SUCCESS",

  "inference_error": null,

  "object_type": "pipe",

  "object_condition": "NORMAL",

  "outputs": {},

  "feedback": [

    {

      "feedback_id": 1,

      "prediction_result": "correct",

      "review_state": "NORMAL_CASE",

      "reviewed_by": "inspector_03",

      "reviewed_at": "2026-04-09T15:20:00+07:00",

      "comment": "Reviewer confirms normal condition",

      "actual_object_condition": "NORMAL",

      "actual_outputs": {}

    }

  ]

}

```

### Feedback Example (Dismissed Case)

```json

{

  "detection_id": 2,

  "inference_status": "SUCCESS",

  "inference_error": null,

  "object_type": "control_valve",

  "object_condition": "ABNORMAL",

  "outputs": {

    "abnormality_type": "oil_leak",

    "severity": "low",

    "confidence": 0.78

  },

  "feedback": [

    {

      "feedback_id": 1,

      "prediction_result": "over_detected",

      "review_state": "DISMISSED_CASE",

      "reviewed_by": "inspector_04",

      "reviewed_at": "2026-04-09T15:30:00+07:00",

      "comment": "Over-detected case caused by stain or reflection",

      "actual_object_condition": "NORMAL",

      "actual_outputs": {}

    }

  ]

}

```

### Feedback Example (Remediated Case)

```json

{

  "detection_id": 2,

  "inference_status": "SUCCESS",

  "inference_error": null,

  "object_type": "control_valve",

  "object_condition": "ABNORMAL",

  "outputs": {

    "abnormality_type": "oil_leak",

    "severity": "low",

    "confidence": 0.78

  },

  "feedback": [

    {

      "feedback_id": 1,

      "prediction_result": "correct",

      "review_state": "REMEDIATED_CASE",

      "reviewed_by": "maintenance_01",

      "reviewed_at": "2026-04-09T16:00:00+07:00",

      "comment": "Leak was valid but has already been remediated",

      "actual_object_condition": "NORMAL",

      "actual_outputs": {}

    }

  ]

}

```

### Failed Case Example

```json

{

  "detection_id": 1,

  "inference_status": "FAILED",

  "inference_error": {

    "code": "IMAGE_QUALITY_TOO_LOW",

    "message": "The inspected region is too blurred for anomaly classification",

    "stage": "classification"

  },

  "object_type": "pipe",

  "object_condition": null,

  "primary_detection": {

    "class_name": "Pipe",

    "class_id": 2,

    "confidence": 0.89,

    "bbox": [

      60,

      220,

      310,

      285

    ]

  },

  "components": {},

  "ocr": [],

  "outputs": {},

  "feedback": [],

  "debug": null

}

```

## D. Scanning Devices (Object Detection)

```jsonc

{

  "inference_request_id": "c79d7c7a-3797-401a-90e1-1f1f2b77e7f0",

  "timestamp": "2026-03-26T19:20:05.112+07:00",

  "image_uri": "s3://robot-1:9090/snapshots/e29963cc-3661-4646-8f7c-a4a149f9464b.png",

  "inference_task": 5,

  "results": [

    {

      "detection_id": 1,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "digital_gauge",

      "object_condition": null,

      "primary_detection": {

        "class_name": "digital-gauge",

        "class_id": 0,

        "confidence": 0.95,

        "bbox": [

          150,

          200,

          350,

          400

        ]

      },

      "components": {},

      "ocr": [],

      "outputs": {},

      "feedback": [],

      "debug": null

    },

    {

      "detection_id": 2,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "analog_gauge",

      "object_condition": null,

      "primary_detection": {

        "class_name": "analog-gauge",

        "class_id": 1,

        "confidence": 0.89,

        "bbox": [

          500,

          100,

          650,

          250

        ]

      },

      "components": {},

      "ocr": [],

      "outputs": {},

      "feedback": [],

      "debug": null

    }

  ]

}

```

### Data Dictionary

| Field | Description | Example |

| :--- | :--- | :--- |

| **`results[].detection_id`** | Object reference ID in the image. | `1`, `2` |

| **`results[].object_type`** | Normalized detected object type. | `digital_gauge`, `analog_gauge` |

| **`results[].object_condition`** | Optional object-level condition. Use `null` if the task only detects device type. | `null` |

| **`results[].primary_detection.class_name`** | Raw class label from the detection model. | `digital-gauge`, `analog-gauge` |

| **`results[].primary_detection.class_id`** | Numeric class ID from the model. | `0`, `1` |

| **`results[].primary_detection.confidence`** | Detection confidence score. | `0.95` |

| **`results[].primary_detection.bbox`** | Bounding box of the detected object. | `[150, 200, 350, 400]` |

### Failed Case Example

```json

{

  "detection_id": 3,

  "inference_status": "FAILED",

  "inference_error": {

    "code": "UNSUPPORTED_CLASS_ID",

    "message": "Detected class could not be mapped to a supported object type",

    "stage": "postprocessing"

  },

  "object_type": "unknown_device",

  "object_condition": null,

  "primary_detection": {

    "class_name": "device_unknown",

    "class_id": 99,

    "confidence": 0.87,

    "bbox": [

      700,

      120,

      860,

      300

    ]

  },

  "components": {},

  "ocr": [],

  "outputs": {},

  "feedback": [],

  "debug": null

}

```

## E. OCR-Only Text Extraction (User-Cropped Input)

This task is intended for cases where the user already crops the region of

interest, such as an equipment nameplate, tag plate, or label, and the AI model

only needs to extract text.

### Recommended Structure

```jsonc

{

  "inference_request_id": "c17a3d16-9e9a-4c1f-8d3f-7d2f4a52e1d1",

  "timestamp": "2026-04-07T14:30:12.112+07:00",

  "image_uri": "s3://robot-1:9090/crops/nameplate_001.png",

  "inference_task": 6,

  "results": [

    {

      "result_id": 1,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "nameplate",

      "source_region": {

        "bbox": null,

        "crop_provided_by_user": true

      },

      "ocr": {

        "text": "P-101A",

        "text_lines": [

          "P-101A"

        ],

        "confidence": 0.98,

        "language": "en"

      },

      "normalized": {

        "text": "P-101A"

      },

      "debug": null

    }

  ]

}

```

### Data Dictionary

| Field | Description | Example |

| :--- | :--- | :--- |

| **`results[].result_id`** | Stable result reference ID when there is no detection stage. | `1` |

| **`results[].object_type`** | Normalized type of cropped object. | `nameplate`, `equipment_tag`, `label` |

| **`results[].source_region`** | Metadata describing the source crop. | `{ "crop_provided_by_user": true }` |

| **`results[].source_region.bbox`** | Original bounding box in the full image if available; otherwise `null`. | `[120, 80, 310, 145]` |

| **`results[].ocr.text`** | Full OCR text extracted from the crop. | `"P-101A"` |

| **`results[].ocr.text_lines`** | OCR output separated by lines. | `["PUMP NO: P-101A", "AREA: WH-03"]` |

| **`results[].ocr.confidence`** | OCR confidence score. | `0.98` |

| **`results[].normalized`** | Optional parsed result derived from OCR output for downstream use. | `{ "equipment_tag": "P-101A" }` |

### Multi-Line Example

```json

{

  "result_id": 1,

  "inference_status": "SUCCESS",

  "inference_error": null,

  "object_type": "nameplate",

  "source_region": {

    "bbox": null,

    "crop_provided_by_user": true

  },

  "ocr": {

    "text": "PUMP NO: P-101A\nAREA: WH-03",

    "text_lines": [

      "PUMP NO: P-101A",

      "AREA: WH-03"

    ],

    "confidence": 0.95,

    "language": "en"

  },

  "normalized": {

    "equipment_tag": "P-101A",

    "area": "WH-03"

  },

  "debug": null

}

```

### Failed Case Example

```json

{

  "result_id": 1,

  "inference_status": "FAILED",

  "inference_error": {

    "code": "TEXT_NOT_READABLE",

    "message": "The cropped image is blurred or has insufficient contrast",

    "stage": "ocr"

  },

  "object_type": "nameplate",

  "source_region": {

    "bbox": null,

    "crop_provided_by_user": true

  },

  "ocr": null,

  "normalized": null,

  "debug": null

}

```

### Design Notes

1. OCR-only tasks should still use the same top-level envelope as other

   inference tasks.

2. OCR-only tasks do **not** need `detection_id`, `primary_detection`,

   `components`, or `outputs` if those fields have no meaning in the pipeline.

3. Use `result_id` instead of `detection_id` when there is no object detection

   stage.

4. Use `source_region` instead of `primary_detection` when the crop is

   user-provided or externally generated.

5. `normalized` is optional and should only be used when downstream systems

   benefit from parsed text fields.

6. Since feedback in this revision is focused on final reviewed results and is

   represented as `feedback[]`, OCR-only tasks may omit `feedback` unless a

   separate text-review schema is needed.

## F. Gas Detection

This task is recommended for **scene-level or area-level gas event detection**.

It may use `result_id` instead of `detection_id` when the result is not tied to

a single detected object.

### Recommended Structure

```jsonc

{

  "inference_request_id": "gas-req-001",

  "timestamp": "2026-04-09T17:00:00+07:00",

  "image_uri": "s3://robot-1:9090/snapshots/raw/e29963cc-3661-4646-8f7c-a4a149f9464b.png",

  "inference_task": 7,

  "results": [

    {

      "result_id": 1,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "gas_monitoring_area",

      "object_condition": "ABNORMAL",

      "outputs": {

        "gas_detected": true,

        "confidence": 0.50

      },

      "feedback": [],

      "debug": null

    }

  ]

}

```

### Data Dictionary

| Field | Description | Example |

| :--- | :--- | :--- |

| **`results[].result_id`** | Stable result reference ID for a scene-level gas result. | `1` |

| **`results[].object_type`** | Normalized scene or area type. | `gas_monitoring_area` |

| **`results[].object_condition`** | Final AI interpretation of the monitored area. | `NORMAL`, `ABNORMAL` |

| **`results[].outputs`** | Gas event outputs for the area, as a flat object. Use `{}` when no gas event is detected. | See output keys below. |

| **`results[].outputs.gas_detected`** | Whether gas was detected. | `true`, `false` |

| **`results[].outputs.confidence`** | Confidence of the gas event classification. | `0.50` |

### Normal Case Example

```json

{

  "result_id": 1,

  "inference_status": "SUCCESS",

  "inference_error": null,

  "object_type": "gas_monitoring_area",

  "object_condition": "NORMAL",

  "outputs": {},

  "feedback": [],

  "debug": null

}

```

### Failed Case Example

```json

{

  "result_id": 1,

  "inference_status": "FAILED",

  "inference_error": {

    "code": "GAS_EVENT_NOT_EVALUABLE",

    "message": "Gas event could not be evaluated from the available frames",

    "stage": "classification"

  },

  "object_type": "gas_monitoring_area",

  "object_condition": null,

  "outputs": {},

  "feedback": [],

  "debug": null

}

```

### Feedback History Example

```json

{

  "feedback": [

    {

      "feedback_id": 1,

      "prediction_result": "correct",

      "review_state": "CONFIRMED_CASE",

      "reviewed_by": "operator_01",

      "reviewed_at": "2026-04-09T17:20:00+07:00",

      "comment": "Gas plume confirmed by operator",

      "actual_object_condition": "ABNORMAL",

      "actual_outputs": {

        "gas_detected": true

      }

    }

  ]

}

```

### Design Notes

1. Use `result_id` when gas detection is scene-level or area-level.

2. If a future gas model also localizes a concrete object or region as the main

   grouping target, `detection_id` may be used instead.

3. Avoid using a separate flat `status_code` when the meaning is already

   captured by `inference_status` and `inference_error`.

4. Use `outputs = {}` for normal cases where no gas event is detected.

5. Use `overlay_image_uri` inside evidence when the overlay artifact is distinct

   from the main input image.

## G. Water Level Estimation

This task is recommended for **discrete water-level estimation** where the AI

predicts a final level class such as `LEVEL_1`, `LEVEL_2`, or `LEVEL_3`.

### Recommended Structure

```jsonc

{

  "inference_request_id": "water-req-001",

  "timestamp": "2026-04-09T17:00:00+07:00",

  "image_uri": "s3://robot-1:9090/snapshots/e29963cc-3661-4646-8f7c-a4a149f9464b.png",

  "inference_task": 8,

  "results": [

    {

      "result_id": 1,

      "inference_status": "SUCCESS",

      "inference_error": null,

      "object_type": "sump",

      "object_condition": "NORMAL",

      "outputs": {

        "sump_type": "cutting_pit",

        "water_level": "normal",

        "confidence": 0.78

      },

      "feedback": [],

      "debug": null

    }

  ]

}

```

### Data Dictionary

| Field | Description | Example |

| :--- | :--- | :--- |

| **`results[].result_id`** | Stable result reference ID for a sump-level result when no object detector is used. | `1` |

| **`results[].object_type`** | Normalized monitored asset type. | `sump` |

| **`results[].outputs`** | AI task outputs for the water level result, as a flat object. | See output keys below. |

| **`results[].outputs.sump_type`** | Human-readable sump type label. | `cutting_pit`, `drain_sump_old`, `drain_sump_new` |

| **`results[].outputs.water_level`** | Stable water-level label. | `LEVEL_1`, `LEVEL_2`, `LEVEL_3` |

| **`results[].outputs.confidence`** | Combined confidence of the water-level classification. | `0.78` |

### Recommended Enum Mapping

#### `sump_type`

- `0` = `cutting_pit`

- `1` = `drain_sump_old`

- `2` = `drain_sump_new`

#### `water_level` value

- `LEVEL_1` = `Low` threshold

- `LEVEL_2` = `Normal` threshold

- `LEVEL_3` = `High` threshold

### Failed Case Example

When water level cannot be estimated, do not use sentinel values such as `-1`.

Instead, use `inference_status` and `inference_error`.

```json

{

  "result_id": 1,

  "inference_status": "FAILED",

  "inference_error": {

    "code": "WATER_LEVEL_NOT_DETECTED",

    "message": "Water level could not be estimated from the image",

    "stage": "classification"

  },

  "object_type": "sump",

  "object_condition": null,

  "outputs": {},

  "feedback": [],

  "debug": null

}

```

### Feedback History Example

```json

{

  "feedback": [

    {

      "feedback_id": 1,

      "prediction_result": "under_detected",

      "review_state": "CONFIRMED_CASE",

      "reviewed_by": "operator_01",

      "reviewed_at": "2026-04-09T17:20:00+07:00",

      "comment": "Actual water level checked on site",

      "actual_object_condition": "ABNORMAL",

      "actual_outputs": {

        "water_level": "LEVEL_3"

      }

    }

  ]

}

```

### Design Notes

1. Water level should be represented under `outputs`, not a separate

   `measurements` field.

2. Use stable enum-style labels such as `LEVEL_1`, `LEVEL_2`, and `LEVEL_3` for

   the `water_level` output value.

3. Avoid sentinel values such as `-1` for undetectable cases. Use

   `inference_status = "FAILED"` and populate `inference_error` instead.

4. `object_condition` may be used to communicate the operational interpretation

   of the sump, while `outputs.water_level` carries the discrete water-level

   output.

5. If a future implementation includes an explicit sump detector, `detection_id`

   and `primary_detection` may be added without changing the rest of the output

   structure.

## Recommended Field Mapping from the Previous Version

| Previous Structure | Revised Structure |

| :--- | :--- |

| `status` | `results[].inference_status` |

| `error_detail` | `results[].inference_error` |

| `detections[]` | `results[].primary_detection` and/or `results[].components` |

| `digital_gauge_results[]` | `results[].outputs` (flat object) |

| `analog_gauge_results[]` | `results[].outputs` (flat object) + `results[].debug` |

| `segmentations[]` | `results[].components` |

| `ocr_results[]` | `results[].ocr` |

| `anomaly_results[]` | `results[].object_condition` + `results[].outputs` |

| `measurements` | `results[].outputs` |

| `findings[]` | `results[].outputs` |

| User feedback / actual value history | `results[].feedback[]`, scoped by `results[].detection_id` or `results[].result_id` |

| Gas detection payload | `results[].object_condition` + `results[].outputs` |

| Water level payload | `results[].outputs.water_level` |

| OCR-only cropped input | `results[].result_id` + `results[].source_region` + `results[].ocr` |

| `outputs[]` (key-value array, v7) | `outputs` (flat object, v8) |

| `false_positive`, `false_negative` (v7) | `over_detected`, `under_detected`, `misclassified` (v8) |

## Notes for Backend and Frontend Implementation

1. Keep the **top-level envelope** consistent across all tasks.

2. `inference_status` should describe inference pipeline execution only.

3. `inference_error` should contain the machine-readable and human-readable

   reason when inference is `PARTIAL` or `FAILED`.

4. For object-detection tasks, `detection_id` should remain the main reference

   key for object-level grouping.

5. For scene-level, event-level, or OCR-only tasks without object detection, use

   `result_id` as the main reference key.

6. `object_condition` should be shown near `object_type` for quick readability.

7. For abnormality tasks:

   - `object_condition = "NORMAL"` should pair with `outputs = {}`

   - `object_condition = "ABNORMAL"` should pair with one or more keys in

     `outputs`

   - `outputs` should be a flat object containing only the task-specific

     payload, such as `abnormality_type`, `severity`, `confidence`, and other

     task-specific fields. A single `confidence` key represents the overall

     confidence for the finding.

8. For gauge-reading and water-level tasks, `outputs` should represent the AI

   measurement result using task-specific keys such as `gauge_reading`,

   `gauge_level`, and `water_level`.

9. For gas-detection tasks, `outputs` should represent gas events using keys

   such as `gas_detected`.

10. If a component cannot be found in a detection-based task, keep the key and

    set the value to `null`.

11. If a list has no entries, use `[]` instead of omitting the field. If an

    object has no entries, use `{}` instead of omitting the field.

12. Keep `class_name` and `class_id` in `primary_detection`, and keep

    `confidence` where relevant, for traceability, debugging, and retraining

    support.

13. `feedback` should be optional, stored as an append-only array inside each

    `results[]` item, and should preserve human-reviewed final results without

    overwriting inference outputs. For detection-based tasks, keep feedback

    under the same `detection_id`; for result-based tasks, keep feedback under

    the same `result_id`.

14. Do not force OCR-only tasks to include meaningless detection fields such as

    `primary_detection: null` unless your implementation requires a single rigid

    schema for validation.

15. **`outputs` is now a flat object instead of a key-value array.** This makes

    downstream consumption simpler since fields can be accessed directly by name

    (e.g. `outputs.gauge_reading`) instead of searching an array. The same

    applies to `actual_outputs` inside feedback records.

16. **`prediction_result` uses operator-friendly terms** instead of statistical

    ML terms: `correct`, `over_detected`, `under_detected`, `misclassified`.

    These read more naturally for inspectors and operators than `false_positive`

    / `false_negative`.

🌟 คอนเซปต์หลักของการอัปเดต Version 8
จุดประสงค์หลักของเวอร์ชันนี้คือการทำให้โครงสร้างข้อมูลเป็นมาตรฐานเดียวกันทุกโมเดล และให้ระบบปลายทาง (เช่น Frontend หรือ Database) นำข้อมูลไปใช้ต่อได้ง่ายที่สุด โดยมีการเปลี่ยนแปลงสำคัญ 3 ส่วนครับ:

outputs กลายเป็น Flat Object: ยกเลิกระบบ Array แบบเดิม ทำให้สามารถดึงค่าได้ตรงๆ เช่น outputs.gauge_reading

แยกสถานะชัดเจน: แยกเรื่อง "AI รันผ่านไหม" (inference_status) ออกจาก "ของที่ตรวจเจอพังไหม" (object_condition) อย่างเด็ดขาด

ระบบ feedback แบบ Append-only: เก็บประวัติการตรวจยืนยันของคน (Operator) เป็น Array ซ้อนไว้ เพื่อดูประวัติการแก้ไขได้โดยไม่ทับข้อมูลผลลัพธ์ดั้งเดิมของ AI

📦 1. โครงสร้างเปลือกนอก (Common Envelope)
ทุกๆ Task จะต้องใช้โครงสร้างครอบด้านนอกเหมือนกันหมด ดังนี้:

inference_request_id: รหัสอ้างอิงของงาน

timestamp: เวลาที่รันผลสำเร็จ

image_uri: ลิงก์รูปภาพที่ใช้

inference_task: รหัสประเภทงาน (0-8)

results: Array ที่เก็บผลลัพธ์ที่ตรวจเจอ (1 วัตถุ = 1 Item ใน Array)

🔍 2. โครงสร้างภายใน results[] (หัวใจสำคัญ)
ข้อมูลใน results จะแบ่งเป็น 2 รูปแบบหลักๆ ตามลักษณะงาน:

แบบที่ 2.1 งานที่ต้องตีกรอบวัตถุ (Detection-Based)
เช่น อ่านเกจ (Gauge), หาความผิดปกติ (Abnormality)

detection_id: รหัสอ้างอิงของวัตถุที่เจอ

primary_detection: พิกัดกรอบ (bbox) และความมั่นใจ

components: ชิ้นส่วนย่อย เช่น เข็ม, หน้าปัดจอ

แบบที่ 2.2 งานภาพรวมหรือ ครอปมาแล้ว (Scene / OCR-Only)
เช่น ตรวจก๊าซรั่วทั้งภาพ (Gas), อ่านป้ายชื่อ (OCR)

result_id: ใช้แทน detection_id

(ตัดพวก primary_detection ทิ้งไปได้เลย ไม่ต้องส่งมา)

ฟิลด์ที่ต้องมีในทั้ง 2 รูปแบบ:

inference_status: รัน AI สำเร็จไหม (SUCCESS, PARTIAL, FAILED)

inference_error: ถ้า FAILED ให้ใส่รายละเอียดสาเหตุมาด้วย

object_type: ประเภทของวัตถุ (เช่น digital_gauge, flange)

object_condition: สภาพของวัตถุ (NORMAL, ABNORMAL หรือ null)

outputs: ก้อน Flat Object ที่เก็บค่าเฉพาะเจาะจงของแต่ละงาน (ถ้าไม่มีผลลัพธ์ให้ใส่ {})

feedback: ก้อน Array เก็บประวัติการ Review จากคน (ถ้ายังไม่มีใครตรวจให้ใส่ [])

📝 3. ตัวอย่างการใช้ outputs ของแต่ละงาน (Task)
ก้อน outputs จะเปลี่ยนรูปร่างไปตามประเภทงาน เพื่อให้ระบบดึงค่าไปโชว์ได้ง่ายที่สุด:

เกจตัวเลข/เข็ม (Digital/Analog Gauge):
{ "gauge_reading": 120.5, "unit": "psi", "gauge_level": "Normal" }

ความผิดปกติ (Abnormality):
{ "abnormality_type": "oil_leak", "severity": "LOW", "confidence": 0.78 }

ก๊าซรั่ว (Gas Detection):
{ "gas_detected": true, "confidence": 0.50 }

ระดับน้ำ (Water Level):
{ "sump_type": "cutting_pit", "water_level": "LEVEL_2" }

👤 4. ระบบแจ้งผลตอบกลับ (Feedback System)
ถูกออกแบบมาเพื่อเก็บ History การทำงานของ Operator โดยเฉพาะ โดยจะซ้อนอยู่ในแต่ละ detection_id หรือ result_id ประกอบด้วย:

prediction_result: คนประเมินผล AI ว่ายังไง (correct ถูกแล้ว, over_detected ทักมั่ว, under_detected หาไม่เจอ, misclassified ทายผิดประเภท)

review_state: สถานะการตรวจสอบ (CONFIRMED_CASE, REMEDIATED_CASE, DISMISSED_CASE, NORMAL_CASE)

actual_object_condition: ค่าความปกติ/ผิดปกติที่คนคอนเฟิร์ม

actual_outputs: ค่าที่คนคอนเฟิร์มว่าถูกต้องจริงๆ (โครงสร้างเหมือน outputs ของ AI เป๊ะๆ)
