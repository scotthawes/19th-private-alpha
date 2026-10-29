# 19th MCP

Connect your agent to 19th to turn your data into machine learning models. Describe what you want to predict, prepare your data, and train a model—all from your conversation.

## Connecting an agent?

Set up the connection for your client, verify access, and help the user find a useful first model. If they already have a prediction in mind, continue with it. Respect requests for setup only.

[Open the 19th dashboard](https://app.19th.com) to sign in, or choose **Sign up** and complete email verification to create your account. If you were invited to a team, use the invited email address. Then complete OAuth in your MCP client; no API key is required. See [account access](/docs#get-access) if you need help signing in or reaching your workspace.

### Connection details

| Setting | Value |
| --- | --- |
| Server name | `19th` |
| Server URL | `https://app.19th.com/mcp` |
| Transport | Streamable HTTP |
| Authentication | OAuth through your MCP client |

Before adding a server, check whether this endpoint is already configured. Reuse an existing connection and preserve other client settings.

### Codex

When the Codex CLI is available, add the server:

```sh
codex mcp add 19th --url https://app.19th.com/mcp
```

If Codex starts an authorization flow, follow it. To sign in or authorize an existing connection, run:

```sh
codex mcp login 19th
```

Check the running command's result before opening an authorization link yourself. If authorization has already completed, continue to verification. See [Codex’s MCP instructions](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) for client details.

If the CLI is unavailable, use the client's MCP connection settings with the endpoint above. Once the tools are available, follow **Train your model** below.

### Claude Code

Add the server to your user configuration:

```sh
claude mcp add --transport http --scope user 19th https://app.19th.com/mcp
```

This makes the connection available across your local projects. Use the user's chosen configuration scope if they specified one.

In Claude Code, open `/mcp`, select `19th`, and complete authentication if prompted. Then follow **Train your model** below. See [Claude Code's MCP instructions](https://code.claude.com/docs/en/mcp) for client details.

### Cursor

Add this entry to `mcpServers` in `~/.cursor/mcp.json` for a connection available across projects. Merge it with existing entries:

```json
{
  "mcpServers": {
    "19th": {
      "url": "https://app.19th.com/mcp"
    }
  }
}
```

For a project-specific connection, use `.cursor/mcp.json` in that project instead. Complete the sign-in flow in Cursor's MCP settings, then follow **Train your model** below. See [Cursor's MCP instructions](https://cursor.com/docs/mcp) for client details.

### Devin

In Devin, open **Customize → MCPs → Add MCP → Add custom MCP**. Name the server `19th`, choose **HTTP**, and enter `https://app.19th.com/mcp` as the server URL. Choose **OAuth** and **Personal** access for your own account, then save and connect.

Complete authorization when prompted and use **Test tools** to check discovery. Once the tools are available in your session, follow **Train your model** below to verify project access. Adding custom servers requires the **Manage MCP Servers** permission. See [Devin’s MCP instructions](https://docs.devin.ai/work-with-devin/mcp).

### Other MCP clients

Add a remote Streamable HTTP server using the endpoint above, then complete the client's OAuth flow. Some apps require the user to add a connection in settings. Guide them through that step and resume verification when the tools become available.


## Train your model

### 1. Read the guide and verify access

Call `get_skill` with no arguments to read the workflow, then `get_capabilities` to verify access and list supported tasks, file formats and training modes. Resolve any access issues before preparing data, and use the tool schemas returned by the connection.

### 2. Find a useful first model

Use what you know from the conversation to suggest up to three useful predictions. Explain what each does and the data it needs, then recommend a starting point. Continue with an established goal without asking the user to repeat it. Use `list_runs` when there is relevant work to resume.

For explicit training tasks, choose the answer you want:

<div class="mcp-prediction-types">

| `prediction.task` | Output | Declaration |
| --- | --- | --- |
| `binary` | `class_label` or `event_probability` | One target; exact typed `positive_label` for probability |
| `multiclass` | `class_label` | One target with three or more categories |
| `regression` | `numeric_value` | One numeric target |
| `ordinal` | `ordered_class` | One target and explicit typed `order` |
| `count` | `count_value` | One nonnegative whole-value target |
| `multilabel` | `label_set` | Ordered `target_columns`; omit `target_column` |
| `ranking` | `ranking_score` | Relevance target, `group_column`, optional `candidate_column`; metadata excluded from inputs |

For ordered categories, declare `order` using typed values such as `{ "type": "string", "value": "low" }`. Preserve category and label order in returned predictions. 19th can help label unlabeled examples for category or probability predictions. Preserve any existing labels.

</div>

### 3. Prepare your data

Follow the guide to prepare one table with the target and inputs available when prediction happens. Preserve supplied labels and unlabeled examples. Read `define-prediction` or `training-data` when you need help with the prediction or preparation.

Use `prep_run` with `action: "template"` for examples matching the connection. Explicit tasks use CSV, its measured byte count and SHA-256 `content_digest` prefixed `sha256:`. Use the supported workflows, formats and training modes listed by `get_capabilities`.

### 4. Upload and review

Upload the file using the returned instructions, then finalize the same preparation with `prep_run`. Follow its status until ready and resolve any issues. Review the target, inputs and `offered_modes` returned for that preparation. Explain the relevant tradeoffs if the user's preference is unclear; continue when their instructions settle the choice.

### 5. Train and follow progress

Call `submit_run` with the ready preparation, a short run name and an offered mode, within the user's authorization. Use `get_results` with the returned `run_id` to follow progress. Follow its next action, wait value and backoff; a timeout leaves the run running. Retry an uncertain submission with the original key and exact arguments.

### 6. Review and use your model

Present the model choices returned for this run, including available Fast, Turbo and Warpspeed variants, previews and ready download links. Fast is the default. Use `get_model` with the returned `run_id` and `model_id` when a selection needs retrieval or a fresh link. Help the user try the model in their project, using `get_runtimes` for a compatible SDK and setup instructions.

## Common use cases

### Find a useful first model

Start with the work already in your conversation. Your agent can suggest a few focused applications, explain the data each needs, and recommend one to try first.

> Based on what you know about my project, suggest three models I could build with 19th. Prioritize ideas where I already have useful data.

### Predict an outcome

Use examples of past outcomes to learn which new cases are likely to have the same result. A starting point might be purchase conversion, customer churn, or whether a support ticket needs escalation.

> I have customer activity and cancellation history. Help me plan a model that predicts cancellation within the next 30 days using information available before that period.

### Estimate a number

Explore a model for a quantity such as delivery duration or job completion time. Start by defining when the prediction will be made and which inputs will be available then.

> I have records of completed deliveries. Help me predict delivery duration from the information we know when an order is placed.

### Categorize messages

Use labels and numeric features you have prepared from messages to train a routing model. The CSV training workflow does not model raw free text. Your application must produce the same features for new messages before making predictions.

> I have numeric features extracted from support messages and labels for the right team. Help me prepare a routing model and check that I can produce the same inputs for new messages.

### Understand a dataset before training

Bring a dataset and an objective. Your agent can work with 19th to clarify the target, create a plan, and explain how the model will be evaluated.

> Use this dataset to help me plan a model for [outcome]. Explain the proposed inputs, evaluation, and any questions we need to resolve before training.

### Take a trained model into your project

Once you have selected a candidate, your agent can retrieve its model bundle and help you work out how to use it in your application.

> Download the selected model from this run. Inspect the bundle and explain what is needed to use it in my project.

These are starting points. The data, task, and available capabilities determine what can be trained and how well it works. Your agent should check the fit before promising an outcome.

## Tools your agent can use

Your agent uses these tools to prepare data, train and use models, and manage runs. It receives the exact arguments and response schemas from the connected server.

### cancel_run

Request cancellation of a specific run. Supply run_id and idempotency_key. Returns the actual state: cancellation may still be underway, or training may already have completed. Follow get_results for the final outcome; do not describe a cancellation request as confirmed termination. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "idempotency_key": {
      "description": "caller-generated retry key: 1-255 characters of letters, digits, '.', '_', ':' or '-'; reuse it only to retry the identical request",
      "examples": [
        "forecast-upload-2026-09-24-01"
      ],
      "maxLength": 255,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9._:-]{1,255}$",
      "type": "string"
    },
    "run_id": {
      "description": "Exact run UUID returned by submit_run or list_runs; use it unchanged to resume the same run.",
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "run_id",
    "idempotency_key"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "model_options": {
      "additionalProperties": false,
      "properties": {
        "all_sizes": {
          "type": "boolean"
        }
      },
      "required": [
        "all_sizes"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "next_action": {
      "additionalProperties": false,
      "properties": {
        "action": {
          "enum": [
            "template",
            "create",
            "finalize",
            "status"
          ],
          "type": "string"
        },
        "model_id": {
          "type": "string"
        },
        "prep_id": {
          "type": "string"
        },
        "run_id": {
          "type": "string"
        },
        "tool": {
          "enum": [
            "prep_run",
            "submit_run",
            "get_results",
            "get_model"
          ],
          "type": "string"
        },
        "use_new_key": {
          "type": "boolean"
        },
        "wait_seconds": {
          "default": 0,
          "maximum": 25,
          "minimum": 0,
          "type": "integer"
        }
      },
      "required": [
        "tool"
      ],
      "type": "object"
    },
    "prep_id": {
      "type": "string"
    },
    "project": {
      "additionalProperties": false,
      "properties": {
        "created_at": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "project_id": {
          "type": "string"
        },
        "updated_at": {
          "type": "string"
        }
      },
      "required": [
        "project_id",
        "name",
        "created_at",
        "updated_at"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "run_id": {
      "type": "string"
    },
    "run_name": {
      "type": "string"
    },
    "state": {
      "enum": [
        "queued",
        "running",
        "cancelling",
        "succeeded",
        "failed",
        "cancelled"
      ],
      "type": "string"
    },
    "training_mode": {
      "enum": [
        "instant",
        "fast",
        "standard",
        "high",
        "ultra"
      ],
      "type": "string"
    }
  },
  "required": [
    "project",
    "run_name",
    "run_id",
    "prep_id",
    "state",
    "training_mode",
    "next_action"
  ],
  "type": "object"
}
```


### create_project

Create an optional project for grouping related training runs. Supply a short readable name and an idempotency_key. Returns the saved project and its server-generated project_id. Choose the name from the user's goal when they have not supplied one. This groups runs without changing permissions or starting training. Retry an uncertain response with the same key and arguments. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "idempotency_key": {
      "description": "caller-generated retry key: 1-255 characters of letters, digits, '.', '_', ':' or '-'; reuse it only to retry the identical request",
      "examples": [
        "forecast-upload-2026-09-24-01"
      ],
      "maxLength": 255,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9._:-]{1,255}$",
      "type": "string"
    },
    "name": {
      "description": "short readable name from the user's goal; 1 to 80 Unicode characters",
      "maxLength": 80,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "name",
    "idempotency_key"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "created_at": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "project_id": {
      "type": "string"
    },
    "updated_at": {
      "type": "string"
    }
  },
  "required": [
    "project_id",
    "name",
    "created_at",
    "updated_at"
  ],
  "type": "object"
}
```


### get_api_setup

Get the API Keys page link. Share it with the user to create an inference API key in the 19th app. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "instructions": {
      "description": "brief navigation instruction to share with the user",
      "type": "string"
    },
    "url": {
      "description": "API Keys page in the configured 19th app",
      "type": "string"
    }
  },
  "required": [
    "url",
    "instructions"
  ],
  "type": "object"
}
```


### get_capabilities

Discover the model-building capabilities available to this connection: supported prediction outcomes, optional project organization, accepted table formats and restrictions, training modes, model choices and delivery availability. Includes readable choice descriptions and defaults. Does not prepare data or start training. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "available": {
      "type": "boolean"
    },
    "default_mode": {
      "type": "string"
    },
    "delivery": {
      "additionalProperties": false,
      "properties": {
        "all_bundle_runtimes_ready": {
          "type": "boolean"
        },
        "bundle_runtimes_available": {
          "type": "boolean"
        },
        "description": {
          "type": "string"
        },
        "formats": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "integer_export": {
          "type": "string"
        },
        "prediction_api_available": {
          "type": "boolean"
        },
        "runtimes_available": {
          "type": "boolean"
        }
      },
      "required": [
        "formats",
        "integer_export",
        "runtimes_available",
        "bundle_runtimes_available",
        "all_bundle_runtimes_ready",
        "prediction_api_available",
        "description"
      ],
      "type": "object"
    },
    "formats": {
      "items": {
        "type": "string"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "input_families": {
      "items": {
        "type": "string"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "labels": {
      "additionalProperties": false,
      "properties": {
        "description": {
          "type": "string"
        },
        "hosted_provider": {
          "type": "boolean"
        },
        "partial_labels_available": {
          "type": "boolean"
        },
        "zero_label_assistance_available": {
          "type": "boolean"
        }
      },
      "required": [
        "partial_labels_available",
        "zero_label_assistance_available",
        "hosted_provider",
        "description"
      ],
      "type": "object"
    },
    "modes": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "available": {
            "type": "boolean"
          },
          "description": {
            "type": "string"
          },
          "id": {
            "type": "string"
          },
          "model_menu": {
            "type": "string"
          },
          "standard_all_sizes": {
            "type": "boolean"
          },
          "tradeoff": {
            "type": "string"
          }
        },
        "required": [
          "id",
          "description",
          "tradeoff",
          "available",
          "model_menu",
          "standard_all_sizes"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "outcomes": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "available": {
            "type": "boolean"
          },
          "description": {
            "type": "string"
          },
          "model_menu": {
            "type": "string"
          },
          "modes": {
            "items": {
              "type": "string"
            },
            "type": [
              "null",
              "array"
            ]
          },
          "output_kind": {
            "enum": [
              "class_label",
              "event_probability",
              "numeric_value",
              "ordered_class",
              "count_value",
              "label_set",
              "ranking_score"
            ],
            "type": "string"
          },
          "standard_all_sizes": {
            "type": "boolean"
          },
          "tasks": {
            "items": {
              "type": "string"
            },
            "type": [
              "null",
              "array"
            ]
          }
        },
        "required": [
          "output_kind",
          "tasks",
          "description",
          "available",
          "standard_all_sizes",
          "model_menu"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "project_grouping_available": {
      "type": "boolean"
    },
    "project_grouping_description": {
      "type": "string"
    },
    "restrictions": {
      "items": {
        "type": "string"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "unavailable_reason": {
      "type": "string"
    }
  },
  "required": [
    "labels",
    "available",
    "outcomes",
    "formats",
    "restrictions",
    "input_families",
    "default_mode",
    "modes",
    "delivery",
    "project_grouping_available",
    "project_grouping_description"
  ],
  "type": "object"
}
```


### get_download

Read an exact download_id returned by request_download, using the same run_id. This read never prepares or retries a download. Ready returns a short-lived direct GET URL, filename, exact size and SHA-256 outside the file body. Raw is exactly one model file. Verify size and digest after transferring; a returned URL does not prove a completed download. Repeat the original request_download arguments to recover a missing or transiently failed download. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "download_id": {
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    },
    "run_id": {
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "run_id",
    "download_id"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "oneOf": [
    {
      "not": {
        "anyOf": [
          {
            "required": [
              "download"
            ]
          },
          {
            "required": [
              "failure_code"
            ]
          },
          {
            "required": [
              "retryable"
            ]
          }
        ]
      },
      "properties": {
        "state": {
          "const": "preparing"
        }
      }
    },
    {
      "not": {
        "required": [
          "download"
        ]
      },
      "properties": {
        "state": {
          "const": "failed"
        }
      },
      "required": [
        "failure_code",
        "retryable"
      ]
    },
    {
      "not": {
        "anyOf": [
          {
            "required": [
              "failure_code"
            ]
          },
          {
            "required": [
              "retryable"
            ]
          }
        ]
      },
      "properties": {
        "state": {
          "const": "ready"
        }
      }
    }
  ],
  "properties": {
    "download": {
      "additionalProperties": false,
      "properties": {
        "bytes": {
          "type": "integer"
        },
        "content_type": {
          "enum": [
            "application/zip",
            "application/octet-stream"
          ],
          "type": "string"
        },
        "expires_at": {
          "type": "string"
        },
        "filename": {
          "type": "string"
        },
        "method": {
          "enum": [
            "GET"
          ],
          "type": "string"
        },
        "sha256": {
          "pattern": "^[a-f0-9]{64}$",
          "type": "string"
        },
        "url": {
          "type": "string"
        }
      },
      "required": [
        "url",
        "method",
        "expires_at",
        "filename",
        "bytes",
        "sha256",
        "content_type"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "download_id": {
      "type": "string"
    },
    "failure_code": {
      "enum": [
        "DOWNLOAD_UNAVAILABLE",
        "DOWNLOAD_INVALID"
      ],
      "type": "string"
    },
    "retryable": {
      "type": [
        "null",
        "boolean"
      ]
    },
    "run_id": {
      "type": "string"
    },
    "schema_version": {
      "enum": [
        "model_download.v1"
      ],
      "type": "string"
    },
    "selection": {
      "additionalProperties": false,
      "properties": {
        "catalog_version": {
          "type": "string"
        },
        "delivery": {
          "enum": [
            "archive",
            "raw"
          ],
          "type": "string"
        },
        "format": {
          "enum": [
            "tfpb",
            "npz"
          ],
          "type": "string"
        },
        "model_ids": {
          "items": {
            "type": "string"
          },
          "maxItems": 64,
          "minItems": 1,
          "type": "array",
          "uniqueItems": true
        },
        "runtime": {
          "additionalProperties": false,
          "properties": {
            "mode": {
              "enum": [
                "none",
                "selected",
                "all"
              ],
              "type": "string"
            },
            "targets": {
              "items": {
                "type": "string"
              },
              "maxItems": 64,
              "minItems": 1,
              "type": "array",
              "uniqueItems": true
            }
          },
          "required": [
            "mode"
          ],
          "type": "object"
        }
      },
      "required": [
        "model_ids",
        "format",
        "delivery",
        "runtime"
      ],
      "type": "object"
    },
    "state": {
      "enum": [
        "preparing",
        "failed",
        "ready"
      ],
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "run_id",
    "download_id",
    "state",
    "selection"
  ],
  "type": "object"
}
```


### get_download_options

Discover the qualified concrete platform targets for minimal model downloads. Copy runtime_id and catalog_version into request_download. all_runtimes_ready reports whether the complete declared launch set is verified. A listed package does not prove model compatibility or a completed download. This read never prepares files. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "all_runtimes_ready": {
      "type": "boolean"
    },
    "catalog_version": {
      "type": "string"
    },
    "default_format": {
      "enum": [
        "tfpb"
      ],
      "type": "string"
    },
    "deliveries": {
      "items": {
        "enum": [
          "archive",
          "raw"
        ],
        "type": "string"
      },
      "maxItems": 2,
      "minItems": 1,
      "type": "array",
      "uniqueItems": true
    },
    "formats": {
      "items": {
        "enum": [
          "tfpb"
        ],
        "type": "string"
      },
      "maxItems": 1,
      "minItems": 1,
      "type": "array",
      "uniqueItems": true
    },
    "runtime_modes": {
      "items": {
        "enum": [
          "none",
          "selected",
          "all"
        ],
        "type": "string"
      },
      "maxItems": 3,
      "minItems": 1,
      "type": "array",
      "uniqueItems": true
    },
    "runtimes": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "platform": {
            "enum": [
              "python",
              "browser",
              "node",
              "ios",
              "android",
              "raspberry_pi",
              "esp32",
              "c",
              "rust"
            ],
            "type": "string"
          },
          "requirements": {
            "items": {
              "type": "string"
            },
            "type": [
              "null",
              "array"
            ]
          },
          "runtime_api": {
            "enum": [
              "tfp-runtime-0.6",
              "tfp-runtime-0.7",
              "tfp-runtime-0.8"
            ],
            "type": "string"
          },
          "runtime_apis": {
            "items": {
              "enum": [
                "tfp-runtime-0.6",
                "tfp-runtime-0.7",
                "tfp-runtime-0.8"
              ],
              "type": "string"
            },
            "maxItems": 3,
            "minItems": 1,
            "type": "array",
            "uniqueItems": true
          },
          "runtime_id": {
            "type": "string"
          },
          "sdk_version": {
            "type": "string"
          },
          "serving_schema": {
            "enum": [
              "tfp-serving/1",
              "tfp-serving/2",
              "tfp-serving/3"
            ],
            "type": "string"
          },
          "title": {
            "type": "string"
          }
        },
        "required": [
          "runtime_id",
          "platform",
          "title",
          "requirements",
          "sdk_version",
          "serving_schema",
          "runtime_api"
        ],
        "type": "object"
      },
      "maxItems": 64,
      "minItems": 0,
      "type": "array",
      "uniqueItems": true
    },
    "schema_version": {
      "enum": [
        "model_download_options.v1"
      ],
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "catalog_version",
    "default_format",
    "formats",
    "deliveries",
    "runtime_modes",
    "runtimes",
    "all_runtimes_ready"
  ],
  "type": "object"
}
```


### get_model

Retrieve a specific model option's download information or refresh its expired link. Supply run_id and a model_id returned by get_results. Reuse the existing bundle; request preparation or recovery through Platform when needed. Returns preparing, failed or ready, with the selected option's model facts. Ready includes a short-lived download link, expiry, file integrity information, prediction/runtime instructions and results-presentation guidance. Supported models also include an independent preview link. Follow returned next actions and retry delays. A returned link does not prove that bytes were downloaded. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "model_id": {
      "description": "exact model handle returned by get_results; display titles are not identifiers",
      "maxLength": 2048,
      "minLength": 1,
      "type": "string"
    },
    "run_id": {
      "description": "Exact run UUID returned by submit_run or list_runs; use it unchanged to resume the same run.",
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "run_id",
    "model_id"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "egress": {
      "additionalProperties": false,
      "properties": {
        "host": {
          "description": "hostname the caller's environment must reach directly",
          "type": "string"
        },
        "note": {
          "description": "prescriptive direct-transfer and network-egress guidance",
          "type": "string"
        }
      },
      "required": [
        "host",
        "note"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "expires_at": {
      "type": [
        "null",
        "string"
      ]
    },
    "failure_code": {
      "type": "string"
    },
    "formats": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "failure_code": {
            "type": "string"
          },
          "format": {
            "enum": [
              "npz",
              "tfpb",
              "integer_tfpb"
            ],
            "type": "string"
          },
          "sha256": {
            "type": "string"
          },
          "size_bytes": {
            "type": [
              "null",
              "integer"
            ]
          },
          "state": {
            "enum": [
              "ready",
              "failed",
              "not_available",
              "off"
            ],
            "type": "string"
          }
        },
        "required": [
          "format",
          "state"
        ],
        "type": "object"
      },
      "maxItems": 3,
      "minItems": 3,
      "type": [
        "null",
        "array"
      ]
    },
    "hint": {
      "type": "string"
    },
    "instructions": {
      "type": "string"
    },
    "model": {
      "additionalProperties": false,
      "description": "authoritative facts for this exact model option, including its readable name, supplied quality differences, export sizes and prediction times; distinct from ZIP transfer size",
      "properties": {
        "formats": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "availability": {
                "type": "string"
              },
              "failure_code": {
                "type": "string"
              },
              "format": {
                "enum": [
                  "npz",
                  "tfpb",
                  "integer_tfpb"
                ],
                "type": "string"
              },
              "size_bytes": {
                "description": "Exact size in bytes of this model export; not the complete download ZIP size. Present in KB or MB; retain the format in structured data.",
                "minimum": 1,
                "type": "integer"
              },
              "state": {
                "enum": [
                  "ready",
                  "failed",
                  "not_available",
                  "off"
                ],
                "type": "string"
              }
            },
            "required": [
              "format",
              "state",
              "availability"
            ],
            "type": "object"
          },
          "maxItems": 3,
          "minItems": 3,
          "type": [
            "null",
            "array"
          ]
        },
        "inference_identity": {
          "additionalProperties": false,
          "properties": {
            "model_id": {
              "type": "string"
            },
            "model_version_id": {
              "type": "string"
            }
          },
          "required": [
            "model_id",
            "model_version_id"
          ],
          "type": [
            "null",
            "object"
          ]
        },
        "inference_state": {
          "description": "Hosted prediction state, present only with inference_identity. loading: the model is being loaded for hosted predictions, retry in about 1 second; ready: hosted predictions are accepted now; unavailable: hosted prediction is not available for this model, use the download.",
          "enum": [
            "loading",
            "ready",
            "unavailable"
          ],
          "type": "string"
        },
        "model_id": {
          "type": "string"
        },
        "prediction_time": {
          "additionalProperties": false,
          "properties": {
            "basis": {
              "description": "Upstream calculation/source classification for the supplied prediction times. Use the returned presentation guidance when showing results.",
              "enum": [
                "reference_cpu_estimate"
              ],
              "type": "string"
            },
            "batch_1000_ms": {
              "description": "Calculated total prediction time for one batch of 1,000 rows, in milliseconds.",
              "minimum": 0,
              "type": "number"
            },
            "batch_threads": {
              "description": "Reference batch concurrency; metadata for interpreting the batch value.",
              "enum": [
                8
              ],
              "type": "integer"
            },
            "row_ms": {
              "description": "Calculated prediction time for one row, in milliseconds.",
              "minimum": 0,
              "type": "number"
            }
          },
          "required": [
            "row_ms",
            "batch_1000_ms",
            "batch_threads",
            "basis"
          ],
          "type": "object"
        },
        "quality": {
          "additionalProperties": false,
          "properties": {
            "difference_points": {
              "description": "Supplied quality difference in points; retain the upstream comparison without rebasing.",
              "type": "number"
            }
          },
          "required": [
            "difference_points"
          ],
          "type": [
            "null",
            "object"
          ]
        },
        "tier": {
          "type": "string"
        },
        "title": {
          "description": "supplied readable download option name",
          "type": "string"
        }
      },
      "required": [
        "model_id",
        "title",
        "tier",
        "formats"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "model_id": {
      "type": "string"
    },
    "next_action": {
      "additionalProperties": false,
      "properties": {
        "action": {
          "enum": [
            "template",
            "create",
            "finalize",
            "status"
          ],
          "type": "string"
        },
        "model_id": {
          "type": "string"
        },
        "prep_id": {
          "type": "string"
        },
        "run_id": {
          "type": "string"
        },
        "tool": {
          "enum": [
            "prep_run",
            "submit_run",
            "get_results",
            "get_model"
          ],
          "type": "string"
        },
        "use_new_key": {
          "type": "boolean"
        },
        "wait_seconds": {
          "default": 0,
          "maximum": 25,
          "minimum": 0,
          "type": "integer"
        }
      },
      "required": [
        "tool"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "presentation": {
      "additionalProperties": false,
      "description": "server-authored results guidance for the handoff; refreshing this download does not replace the other model choices from get_results",
      "properties": {
        "markdown": {
          "description": "registered presentation guide or applicable sections",
          "type": "string"
        },
        "name": {
          "description": "registered presentation guide name",
          "type": "string"
        },
        "version": {
          "description": "semantic version plus the first eight hex digits of the markdown SHA-256",
          "type": "string"
        }
      },
      "required": [
        "name",
        "version",
        "markdown"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "preview_url": {
      "type": "string"
    },
    "retryable": {
      "type": [
        "null",
        "boolean"
      ]
    },
    "run_id": {
      "type": "string"
    },
    "run_name": {
      "type": "string"
    },
    "runtime": {
      "type": "string"
    },
    "schema_version": {
      "type": "string"
    },
    "sha256": {
      "type": "string"
    },
    "size_bytes": {
      "type": [
        "null",
        "integer"
      ]
    },
    "state": {
      "enum": [
        "preparing",
        "failed",
        "ready"
      ],
      "type": "string"
    },
    "url": {
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "run_name",
    "run_id",
    "model_id",
    "state",
    "runtime",
    "formats",
    "instructions"
  ],
  "type": "object"
}
```


### get_project

Read one project using a project_id returned by list_projects or create_project. Returns its name and saved details. Use list_runs with that project_id to view its runs. Reading a project does not change it or grant access to its runs. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "project_id": {
      "description": "project handle returned by list_projects or create_project",
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "project_id"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "created_at": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "project_id": {
      "type": "string"
    },
    "updated_at": {
      "type": "string"
    }
  },
  "required": [
    "project_id",
    "name",
    "created_at",
    "updated_at"
  ],
  "type": "object"
}
```


### get_results

Read a run's state, model options and downloads. Supply run_id; wait_seconds accepts 0 to 25 and defaults to 0 for an immediate read. A positive value waits for an update or timeout. Results include each available model option's download link once ready, its expiry, quality differences and prediction times when available, and supported preview links. For a completed run with missing bundles, this call can request their preparation through Platform. While downloads are preparing, follow the returned next action; a packaging failure does not mean training failed. Present results using the supplied names and returned presentation guidance. Use get_model to retrieve a specific option or refresh an expired link. Follow explicit retry backoffs. A pending response or timeout never cancels the run or justifies another submission. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "run_id": {
      "description": "Exact run UUID returned by submit_run or list_runs; use it unchanged to resume the same run.",
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    },
    "wait_seconds": {
      "default": 0,
      "description": "0 to 25 seconds; zero or absent returns immediately; positive waits for an update without cancellation or resubmission",
      "maximum": 25,
      "minimum": 0,
      "type": "integer"
    }
  },
  "required": [
    "run_id"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "classes": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "canonical": {
            "type": "string"
          },
          "index": {
            "type": "integer"
          },
          "label": {
            "additionalProperties": false,
            "properties": {
              "type": {
                "type": "string"
              },
              "value": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "boolean"
                  },
                  {
                    "type": "number"
                  }
                ]
              }
            },
            "required": [
              "type",
              "value"
            ],
            "type": "object"
          }
        },
        "required": [
          "index",
          "canonical",
          "label"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "created_at": {
      "type": "string"
    },
    "csv_validation": {
      "additionalProperties": false,
      "properties": {
        "classes": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "canonical": {
                "type": "string"
              },
              "index": {
                "type": "integer"
              },
              "label": {
                "additionalProperties": false,
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "value": {
                    "oneOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "boolean"
                      },
                      {
                        "type": "number"
                      }
                    ]
                  }
                },
                "required": [
                  "type",
                  "value"
                ],
                "type": "object"
              }
            },
            "required": [
              "index",
              "canonical",
              "label"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "effective_inputs": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "dimension": {
                "maximum": 4096,
                "minimum": 1,
                "type": "integer"
              },
              "encoder": {
                "additionalProperties": false,
                "properties": {
                  "instruction": {
                    "type": "string"
                  },
                  "name": {
                    "type": "string"
                  },
                  "revision": {
                    "type": "string"
                  }
                },
                "type": "object"
              },
              "formats": {
                "items": {
                  "type": "string"
                },
                "type": [
                  "null",
                  "array"
                ]
              },
              "kind": {
                "type": "string"
              },
              "name": {
                "type": "string"
              },
              "parts": {
                "items": {
                  "type": "string"
                },
                "type": [
                  "null",
                  "array"
                ]
              }
            },
            "required": [
              "name",
              "kind"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "excluded_inputs": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "column": {
                "type": "string"
              },
              "reason": {
                "type": "string"
              }
            },
            "required": [
              "column",
              "reason"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "generated_labels": {
          "type": [
            "null",
            "integer"
          ]
        },
        "groups": {
          "type": [
            "null",
            "integer"
          ]
        },
        "input_digest": {
          "type": "string"
        },
        "label_coverage": {
          "additionalProperties": false,
          "properties": {
            "labeled": {
              "type": "integer"
            },
            "unlabeled": {
              "type": "integer"
            }
          },
          "required": [
            "labeled",
            "unlabeled"
          ],
          "type": "object"
        },
        "labels": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "positive_class_index": {
          "type": [
            "null",
            "integer"
          ]
        },
        "rows": {
          "type": "integer"
        },
        "schema_version": {
          "type": "string"
        },
        "task": {
          "type": "string"
        },
        "values": {
          "items": {
            "type": "number"
          },
          "type": [
            "null",
            "array"
          ]
        }
      },
      "required": [
        "schema_version",
        "input_digest",
        "rows",
        "label_coverage",
        "effective_inputs",
        "excluded_inputs",
        "task"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "effective_inputs": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "dimension": {
            "maximum": 4096,
            "minimum": 1,
            "type": "integer"
          },
          "encoder": {
            "additionalProperties": false,
            "properties": {
              "instruction": {
                "type": "string"
              },
              "name": {
                "type": "string"
              },
              "revision": {
                "type": "string"
              }
            },
            "type": "object"
          },
          "formats": {
            "items": {
              "type": "string"
            },
            "type": [
              "null",
              "array"
            ]
          },
          "kind": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "parts": {
            "items": {
              "type": "string"
            },
            "type": [
              "null",
              "array"
            ]
          }
        },
        "required": [
          "name",
          "kind"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "excluded_inputs": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "column": {
            "type": "string"
          },
          "reason": {
            "type": "string"
          }
        },
        "required": [
          "column",
          "reason"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "failure": {
      "additionalProperties": false,
      "properties": {
        "code": {
          "type": "string"
        },
        "issues": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "code": {
                "type": "string"
              },
              "column": {
                "type": "string"
              },
              "count": {
                "type": [
                  "null",
                  "integer"
                ]
              },
              "field": {
                "type": "string"
              },
              "hint": {
                "type": "string"
              },
              "message": {
                "type": "string"
              }
            },
            "required": [
              "field",
              "code",
              "message",
              "hint"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "message": {
          "type": "string"
        },
        "retryable": {
          "type": "boolean"
        }
      },
      "required": [
        "code",
        "message",
        "retryable"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "finished_at": {
      "type": [
        "null",
        "string"
      ]
    },
    "model_options": {
      "additionalProperties": false,
      "properties": {
        "all_sizes": {
          "type": "boolean"
        }
      },
      "required": [
        "all_sizes"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "model_previews": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "model_id": {
            "description": "exact model handle returned in models",
            "type": "string"
          },
          "preview_url": {
            "description": "selected-model preview in the signed-in 19th app; navigation conveys no access grant",
            "type": "string"
          }
        },
        "required": [
          "model_id",
          "preview_url"
        ],
        "type": "object"
      },
      "maxItems": 64,
      "type": [
        "null",
        "array"
      ]
    },
    "models": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "delivery_state": {
            "enum": [
              "available",
              "preparing",
              "ready",
              "failed"
            ],
            "type": "string"
          },
          "download": {
            "additionalProperties": false,
            "description": "Download receipt for this exact model option. A ready receipt includes an expiring URL, ZIP byte count, checksum and prediction/setup instructions. Missing or preparing receipts do not provide a download link. Use get_model to refresh or recover this option.",
            "properties": {
              "egress": {
                "additionalProperties": false,
                "properties": {
                  "host": {
                    "description": "hostname the caller's environment must reach directly",
                    "type": "string"
                  },
                  "note": {
                    "description": "prescriptive direct-transfer and network-egress guidance",
                    "type": "string"
                  }
                },
                "required": [
                  "host",
                  "note"
                ],
                "type": [
                  "null",
                  "object"
                ]
              },
              "expires_at": {
                "type": [
                  "null",
                  "string"
                ]
              },
              "failure_code": {
                "type": "string"
              },
              "formats": {
                "items": {
                  "additionalProperties": false,
                  "properties": {
                    "failure_code": {
                      "type": "string"
                    },
                    "format": {
                      "enum": [
                        "npz",
                        "tfpb",
                        "integer_tfpb"
                      ],
                      "type": "string"
                    },
                    "sha256": {
                      "type": "string"
                    },
                    "size_bytes": {
                      "type": [
                        "null",
                        "integer"
                      ]
                    },
                    "state": {
                      "enum": [
                        "ready",
                        "failed",
                        "not_available",
                        "off"
                      ],
                      "type": "string"
                    }
                  },
                  "required": [
                    "format",
                    "state"
                  ],
                  "type": "object"
                },
                "maxItems": 3,
                "minItems": 3,
                "type": [
                  "null",
                  "array"
                ]
              },
              "hint": {
                "type": "string"
              },
              "instructions": {
                "type": "string"
              },
              "model": {
                "additionalProperties": false,
                "description": "authoritative facts for this exact model option, including its readable name, supplied quality differences, export sizes and prediction times; distinct from ZIP transfer size",
                "properties": {
                  "formats": {
                    "items": {
                      "additionalProperties": false,
                      "properties": {
                        "availability": {
                          "type": "string"
                        },
                        "failure_code": {
                          "type": "string"
                        },
                        "format": {
                          "enum": [
                            "npz",
                            "tfpb",
                            "integer_tfpb"
                          ],
                          "type": "string"
                        },
                        "size_bytes": {
                          "description": "Exact size in bytes of this model export; not the complete download ZIP size. Present in KB or MB; retain the format in structured data.",
                          "minimum": 1,
                          "type": "integer"
                        },
                        "state": {
                          "enum": [
                            "ready",
                            "failed",
                            "not_available",
                            "off"
                          ],
                          "type": "string"
                        }
                      },
                      "required": [
                        "format",
                        "state",
                        "availability"
                      ],
                      "type": "object"
                    },
                    "maxItems": 3,
                    "minItems": 3,
                    "type": [
                      "null",
                      "array"
                    ]
                  },
                  "inference_identity": {
                    "additionalProperties": false,
                    "properties": {
                      "model_id": {
                        "type": "string"
                      },
                      "model_version_id": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "model_id",
                      "model_version_id"
                    ],
                    "type": [
                      "null",
                      "object"
                    ]
                  },
                  "inference_state": {
                    "description": "Hosted prediction state, present only with inference_identity. loading: the model is being loaded for hosted predictions, retry in about 1 second; ready: hosted predictions are accepted now; unavailable: hosted prediction is not available for this model, use the download.",
                    "enum": [
                      "loading",
                      "ready",
                      "unavailable"
                    ],
                    "type": "string"
                  },
                  "model_id": {
                    "type": "string"
                  },
                  "prediction_time": {
                    "additionalProperties": false,
                    "properties": {
                      "basis": {
                        "description": "Upstream calculation/source classification for the supplied prediction times. Use the returned presentation guidance when showing results.",
                        "enum": [
                          "reference_cpu_estimate"
                        ],
                        "type": "string"
                      },
                      "batch_1000_ms": {
                        "description": "Calculated total prediction time for one batch of 1,000 rows, in milliseconds.",
                        "minimum": 0,
                        "type": "number"
                      },
                      "batch_threads": {
                        "description": "Reference batch concurrency; metadata for interpreting the batch value.",
                        "enum": [
                          8
                        ],
                        "type": "integer"
                      },
                      "row_ms": {
                        "description": "Calculated prediction time for one row, in milliseconds.",
                        "minimum": 0,
                        "type": "number"
                      }
                    },
                    "required": [
                      "row_ms",
                      "batch_1000_ms",
                      "batch_threads",
                      "basis"
                    ],
                    "type": "object"
                  },
                  "quality": {
                    "additionalProperties": false,
                    "properties": {
                      "difference_points": {
                        "description": "Supplied quality difference in points; retain the upstream comparison without rebasing.",
                        "type": "number"
                      }
                    },
                    "required": [
                      "difference_points"
                    ],
                    "type": [
                      "null",
                      "object"
                    ]
                  },
                  "tier": {
                    "type": "string"
                  },
                  "title": {
                    "description": "supplied readable download option name",
                    "type": "string"
                  }
                },
                "required": [
                  "model_id",
                  "title",
                  "tier",
                  "formats"
                ],
                "type": [
                  "null",
                  "object"
                ]
              },
              "model_id": {
                "type": "string"
              },
              "next_action": {
                "additionalProperties": false,
                "properties": {
                  "action": {
                    "enum": [
                      "template",
                      "create",
                      "finalize",
                      "status"
                    ],
                    "type": "string"
                  },
                  "model_id": {
                    "type": "string"
                  },
                  "prep_id": {
                    "type": "string"
                  },
                  "run_id": {
                    "type": "string"
                  },
                  "tool": {
                    "enum": [
                      "prep_run",
                      "submit_run",
                      "get_results",
                      "get_model"
                    ],
                    "type": "string"
                  },
                  "use_new_key": {
                    "type": "boolean"
                  },
                  "wait_seconds": {
                    "default": 0,
                    "maximum": 25,
                    "minimum": 0,
                    "type": "integer"
                  }
                },
                "required": [
                  "tool"
                ],
                "type": [
                  "null",
                  "object"
                ]
              },
              "presentation": {
                "additionalProperties": false,
                "description": "server-authored results guidance for the handoff; refreshing this download does not replace the other model choices from get_results",
                "properties": {
                  "markdown": {
                    "description": "registered presentation guide or applicable sections",
                    "type": "string"
                  },
                  "name": {
                    "description": "registered presentation guide name",
                    "type": "string"
                  },
                  "version": {
                    "description": "semantic version plus the first eight hex digits of the markdown SHA-256",
                    "type": "string"
                  }
                },
                "required": [
                  "name",
                  "version",
                  "markdown"
                ],
                "type": [
                  "null",
                  "object"
                ]
              },
              "preview_url": {
                "type": "string"
              },
              "retryable": {
                "type": [
                  "null",
                  "boolean"
                ]
              },
              "run_id": {
                "type": "string"
              },
              "run_name": {
                "type": "string"
              },
              "runtime": {
                "type": "string"
              },
              "schema_version": {
                "type": "string"
              },
              "sha256": {
                "type": "string"
              },
              "size_bytes": {
                "type": [
                  "null",
                  "integer"
                ]
              },
              "state": {
                "enum": [
                  "preparing",
                  "failed",
                  "ready"
                ],
                "type": "string"
              },
              "url": {
                "type": "string"
              }
            },
            "required": [
              "schema_version",
              "run_name",
              "run_id",
              "model_id",
              "state",
              "runtime",
              "formats",
              "instructions"
            ],
            "type": [
              "null",
              "object"
            ]
          },
          "formats": {
            "items": {
              "additionalProperties": false,
              "properties": {
                "availability": {
                  "type": "string"
                },
                "failure_code": {
                  "type": "string"
                },
                "format": {
                  "enum": [
                    "npz",
                    "tfpb",
                    "integer_tfpb"
                  ],
                  "type": "string"
                },
                "size_bytes": {
                  "description": "Exact size in bytes of this model export; not the complete download ZIP size. Present in KB or MB; retain the format in structured data.",
                  "minimum": 1,
                  "type": "integer"
                },
                "state": {
                  "enum": [
                    "ready",
                    "failed",
                    "not_available",
                    "off"
                  ],
                  "type": "string"
                }
              },
              "required": [
                "format",
                "state",
                "availability"
              ],
              "type": "object"
            },
            "maxItems": 3,
            "minItems": 3,
            "type": [
              "null",
              "array"
            ]
          },
          "inference_identity": {
            "additionalProperties": false,
            "properties": {
              "model_id": {
                "type": "string"
              },
              "model_version_id": {
                "type": "string"
              }
            },
            "required": [
              "model_id",
              "model_version_id"
            ],
            "type": [
              "null",
              "object"
            ]
          },
          "inference_state": {
            "description": "Hosted prediction state, present only with inference_identity. loading: the model is being loaded for hosted predictions, retry in about 1 second; ready: hosted predictions are accepted now; unavailable: hosted prediction is not available for this model, use the download.",
            "enum": [
              "loading",
              "ready",
              "unavailable"
            ],
            "type": "string"
          },
          "model_id": {
            "type": "string"
          },
          "next_action": {
            "additionalProperties": false,
            "properties": {
              "action": {
                "enum": [
                  "template",
                  "create",
                  "finalize",
                  "status"
                ],
                "type": "string"
              },
              "model_id": {
                "type": "string"
              },
              "prep_id": {
                "type": "string"
              },
              "run_id": {
                "type": "string"
              },
              "tool": {
                "enum": [
                  "prep_run",
                  "submit_run",
                  "get_results",
                  "get_model"
                ],
                "type": "string"
              },
              "use_new_key": {
                "type": "boolean"
              },
              "wait_seconds": {
                "default": 0,
                "maximum": 25,
                "minimum": 0,
                "type": "integer"
              }
            },
            "required": [
              "tool"
            ],
            "type": "object"
          },
          "prediction_time": {
            "additionalProperties": false,
            "properties": {
              "basis": {
                "description": "Upstream calculation/source classification for the supplied prediction times. Use the returned presentation guidance when showing results.",
                "enum": [
                  "reference_cpu_estimate"
                ],
                "type": "string"
              },
              "batch_1000_ms": {
                "description": "Calculated total prediction time for one batch of 1,000 rows, in milliseconds.",
                "minimum": 0,
                "type": "number"
              },
              "batch_threads": {
                "description": "Reference batch concurrency; metadata for interpreting the batch value.",
                "enum": [
                  8
                ],
                "type": "integer"
              },
              "row_ms": {
                "description": "Calculated prediction time for one row, in milliseconds.",
                "minimum": 0,
                "type": "number"
              }
            },
            "required": [
              "row_ms",
              "batch_1000_ms",
              "batch_threads",
              "basis"
            ],
            "type": "object"
          },
          "quality": {
            "additionalProperties": false,
            "properties": {
              "difference_points": {
                "description": "Supplied quality difference in points; retain the upstream comparison without rebasing.",
                "type": "number"
              }
            },
            "required": [
              "difference_points"
            ],
            "type": [
              "null",
              "object"
            ]
          },
          "tier": {
            "type": "string"
          },
          "title": {
            "description": "supplied readable download option name",
            "type": "string"
          }
        },
        "required": [
          "model_id",
          "title",
          "tier",
          "formats",
          "delivery_state",
          "next_action"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "next_action": {
      "additionalProperties": false,
      "properties": {
        "action": {
          "enum": [
            "template",
            "create",
            "finalize",
            "status"
          ],
          "type": "string"
        },
        "model_id": {
          "type": "string"
        },
        "prep_id": {
          "type": "string"
        },
        "run_id": {
          "type": "string"
        },
        "tool": {
          "enum": [
            "prep_run",
            "submit_run",
            "get_results",
            "get_model"
          ],
          "type": "string"
        },
        "use_new_key": {
          "type": "boolean"
        },
        "wait_seconds": {
          "default": 0,
          "maximum": 25,
          "minimum": 0,
          "type": "integer"
        }
      },
      "required": [
        "tool"
      ],
      "type": "object"
    },
    "positive_class_index": {
      "type": [
        "null",
        "integer"
      ]
    },
    "prediction": {
      "additionalProperties": false,
      "properties": {
        "candidate_column": {
          "type": "string"
        },
        "column_types": {
          "additionalProperties": false,
          "maxProperties": 2048,
          "patternProperties": {
            "^": {
              "enum": [
                "vector"
              ],
              "type": "string"
            }
          },
          "propertyNames": {
            "maxLength": 255,
            "minLength": 1,
            "type": "string"
          },
          "type": "object"
        },
        "count_target": {
          "type": "string"
        },
        "group_column": {
          "type": "string"
        },
        "input_columns": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "labeling": {
          "additionalProperties": false,
          "properties": {
            "classes": {
              "items": {
                "additionalProperties": false,
                "properties": {
                  "meaning": {
                    "maxLength": 1000,
                    "type": "string"
                  },
                  "value": {
                    "oneOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "boolean"
                      },
                      {
                        "type": "number"
                      }
                    ]
                  }
                },
                "required": [
                  "value"
                ],
                "type": "object"
              },
              "maxItems": 256,
              "minItems": 2,
              "type": [
                "null",
                "array"
              ]
            },
            "columns": {
              "additionalProperties": false,
              "maxProperties": 2048,
              "patternProperties": {
                "^": {
                  "maxLength": 1000,
                  "minLength": 1,
                  "type": "string"
                }
              },
              "propertyNames": {
                "maxLength": 255,
                "minLength": 1,
                "type": "string"
              },
              "type": "object"
            },
            "description": {
              "maxLength": 4000,
              "minLength": 1,
              "type": "string"
            },
            "outcome_shares": {
              "additionalProperties": false,
              "maxProperties": 256,
              "patternProperties": {
                "^": {
                  "exclusiveMaximum": 1,
                  "exclusiveMinimum": 0,
                  "type": "number"
                }
              },
              "propertyNames": {
                "maxLength": 8192,
                "minLength": 1,
                "type": "string"
              },
              "type": "object"
            }
          },
          "required": [
            "description",
            "classes"
          ],
          "type": [
            "null",
            "object"
          ]
        },
        "order": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "type": {
                "type": "string"
              },
              "value": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "boolean"
                  },
                  {
                    "type": "number"
                  }
                ]
              }
            },
            "required": [
              "type",
              "value"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "output_kind": {
          "enum": [
            "class_label",
            "event_probability",
            "numeric_value",
            "ordered_class",
            "count_value",
            "label_set",
            "ranking_score"
          ],
          "type": "string"
        },
        "pairs": {
          "items": {
            "items": {
              "type": "string"
            },
            "type": [
              "null",
              "array"
            ]
          },
          "type": [
            "null",
            "array"
          ]
        },
        "positive_label": {
          "oneOf": [
            {
              "type": "string"
            },
            {
              "type": "boolean"
            },
            {
              "type": "number"
            }
          ]
        },
        "target_column": {
          "type": "string"
        },
        "target_columns": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "task": {
          "type": "string"
        }
      },
      "required": [
        "input_columns",
        "output_kind"
      ],
      "type": "object"
    },
    "prep_id": {
      "type": "string"
    },
    "presentation": {
      "additionalProperties": false,
      "properties": {
        "markdown": {
          "description": "registered presentation guide or applicable sections",
          "type": "string"
        },
        "name": {
          "description": "registered presentation guide name",
          "type": "string"
        },
        "version": {
          "description": "semantic version plus the first eight hex digits of the markdown SHA-256",
          "type": "string"
        }
      },
      "required": [
        "name",
        "version",
        "markdown"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "preview_url": {
      "type": "string"
    },
    "progress": {
      "additionalProperties": false,
      "properties": {
        "sampled_at": {
          "type": "string"
        },
        "stage": {
          "type": "string"
        },
        "work_units": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "display_value": {
                "type": "string"
              },
              "label": {
                "type": "string"
              },
              "unit": {
                "type": "string"
              },
              "value": {
                "type": "number"
              }
            },
            "required": [
              "label",
              "unit",
              "value",
              "display_value"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        }
      },
      "required": [
        "stage",
        "work_units"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "project": {
      "additionalProperties": false,
      "properties": {
        "created_at": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "project_id": {
          "type": "string"
        },
        "updated_at": {
          "type": "string"
        }
      },
      "required": [
        "project_id",
        "name",
        "created_at",
        "updated_at"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "results_state": {
      "enum": [
        "pending",
        "ready",
        "unavailable"
      ],
      "type": "string"
    },
    "run_id": {
      "type": "string"
    },
    "run_name": {
      "type": "string"
    },
    "schema_version": {
      "type": "string"
    },
    "started_at": {
      "type": [
        "null",
        "string"
      ]
    },
    "state": {
      "enum": [
        "queued",
        "running",
        "cancelling",
        "succeeded",
        "failed",
        "cancelled"
      ],
      "type": "string"
    },
    "suggested_poll_seconds": {
      "type": [
        "null",
        "integer"
      ]
    },
    "task_kind": {
      "enum": [
        "binary",
        "multiclass",
        "regression",
        "ordinal",
        "count",
        "multilabel",
        "ranking"
      ],
      "type": "string"
    },
    "training_mode": {
      "enum": [
        "instant",
        "fast",
        "standard",
        "high",
        "ultra"
      ],
      "type": "string"
    },
    "updated_at": {
      "type": "string"
    },
    "warnings": {
      "items": {
        "type": "string"
      },
      "type": [
        "null",
        "array"
      ]
    }
  },
  "required": [
    "schema_version",
    "results_state",
    "project",
    "run_name",
    "run_id",
    "prep_id",
    "state",
    "training_mode",
    "next_action",
    "created_at",
    "updated_at",
    "effective_inputs",
    "excluded_inputs",
    "prediction",
    "task_kind",
    "warnings",
    "models"
  ],
  "type": "object"
}
```


### get_runtimes

Discover reusable SDK/runtime packages for running downloaded models locally. Call without arguments to get the full supported menu, including each environment's platform requirements. Call again with a runtime_id returned by that menu to get its package download, integrity information and installation/model-loading instructions. Select the target environment of the user's application, not the machine running this agent. Packages are reused across compatible models; this call does not train a model or deploy an API. A returned link does not prove download or installation. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "runtime_id": {
      "description": "Omit to browse. To retrieve a package and setup, copy a runtime_id from the returned menu identifying the exact environment and installation target. Do not invent an ID or supply a URL.",
      "pattern": "^[a-z0-9][a-z0-9._-]{0,127}$",
      "type": "string"
    }
  },
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "oneOf": [
    {
      "not": {
        "anyOf": [
          {
            "required": [
              "runtime"
            ]
          },
          {
            "required": [
              "download"
            ]
          },
          {
            "required": [
              "setup"
            ]
          }
        ]
      },
      "properties": {
        "kind": {
          "const": "menu"
        }
      },
      "required": [
        "kind",
        "catalog_version",
        "runtimes"
      ]
    },
    {
      "not": {
        "required": [
          "runtimes"
        ]
      },
      "properties": {
        "kind": {
          "const": "selection"
        }
      },
      "required": [
        "kind",
        "catalog_version",
        "runtime",
        "download",
        "setup"
      ]
    }
  ],
  "properties": {
    "catalog_version": {
      "type": "string"
    },
    "download": {
      "additionalProperties": false,
      "properties": {
        "bytes": {
          "type": "integer"
        },
        "content_type": {
          "type": "string"
        },
        "expires_at": {
          "type": "string"
        },
        "filename": {
          "type": "string"
        },
        "method": {
          "type": "string"
        },
        "sha256": {
          "type": "string"
        },
        "url": {
          "type": "string"
        }
      },
      "required": [
        "url",
        "method",
        "expires_at",
        "filename",
        "bytes",
        "sha256",
        "content_type"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "kind": {
      "enum": [
        "menu",
        "selection"
      ],
      "type": "string"
    },
    "runtime": {
      "additionalProperties": false,
      "properties": {
        "choose_when": {
          "type": "string"
        },
        "environment": {
          "type": "string"
        },
        "model_contract": {
          "type": "string"
        },
        "model_formats": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "requirements": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "runtime_id": {
          "type": "string"
        },
        "sdk_version": {
          "type": "string"
        },
        "title": {
          "type": "string"
        }
      },
      "required": [
        "runtime_id",
        "title",
        "environment",
        "requirements",
        "sdk_version",
        "model_formats",
        "model_contract",
        "choose_when"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "runtimes": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "choose_when": {
            "type": "string"
          },
          "environment": {
            "type": "string"
          },
          "model_contract": {
            "type": "string"
          },
          "model_formats": {
            "items": {
              "type": "string"
            },
            "type": [
              "null",
              "array"
            ]
          },
          "requirements": {
            "items": {
              "type": "string"
            },
            "type": [
              "null",
              "array"
            ]
          },
          "runtime_id": {
            "type": "string"
          },
          "sdk_version": {
            "type": "string"
          },
          "title": {
            "type": "string"
          }
        },
        "required": [
          "runtime_id",
          "title",
          "environment",
          "requirements",
          "sdk_version",
          "model_formats",
          "model_contract",
          "choose_when"
        ],
        "type": "object"
      },
      "maxItems": 64,
      "type": "array"
    },
    "setup": {
      "additionalProperties": false,
      "properties": {
        "markdown": {
          "type": "string"
        },
        "version": {
          "type": "string"
        }
      },
      "required": [
        "version",
        "markdown"
      ],
      "type": [
        "null",
        "object"
      ]
    }
  },
  "required": [
    "kind",
    "catalog_version"
  ],
  "type": "object"
}
```


### get_skill

Read the default training guide for the workflow. Read define-prediction for unresolved target/output, label-definition or consequential input-scope choices. Read training-data for label coverage/assistance, or before combining sources or changing nulls, duplicates, conflicting labels, types or derived inputs. Guides are versioned; static reads do not verify account access. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "name": {
      "description": "skill name; defaults to training; define-prediction and training-data are conditional references; supported explicit legacy names remain available",
      "type": "string"
    }
  },
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "markdown": {
      "description": "complete customer interaction guide",
      "type": "string"
    },
    "name": {
      "description": "stable skill name",
      "type": "string"
    },
    "updated_at": {
      "description": "guide update date in YYYY-MM-DD format",
      "type": "string"
    },
    "version": {
      "description": "semantic version plus the first eight hex digits of the markdown SHA-256",
      "type": "string"
    }
  },
  "required": [
    "name",
    "version",
    "updated_at",
    "markdown"
  ],
  "type": "object"
}
```


### list_projects

List projects visible to this connection. Projects optionally group multiple training runs. Returns their names and project_id handles, with the most recently updated projects first. Use the returned next_cursor unchanged with the same pagination settings. Listing projects does not start training or change permissions. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "copy next_cursor unchanged with the same pagination settings",
      "maxLength": 4096,
      "minLength": 0,
      "type": "string"
    },
    "limit": {
      "description": "optional page size from 1 to 100; defaults to 20",
      "maximum": 100,
      "minimum": 1,
      "type": "integer"
    }
  },
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "next_cursor": {
      "type": "string"
    },
    "projects": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "created_at": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "project_id": {
            "type": "string"
          },
          "updated_at": {
            "type": "string"
          }
        },
        "required": [
          "project_id",
          "name",
          "created_at",
          "updated_at"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    }
  },
  "required": [
    "projects"
  ],
  "type": "object"
}
```


### list_runs

List runs visible to this connection for history or resumption. Omit project_id for all runs, including those without a project; supply a returned project_id to list that project's runs. Use optional state and pagination fields to narrow the list. Returns run names, run_id handles and saved project assignments. Follow next_cursor unchanged with the same filters; an empty page is not proof that no runs exist. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "description": "copy next_cursor unchanged from previous response with identical filters; do not invent a cursor",
      "maxLength": 4096,
      "minLength": 1,
      "type": "string"
    },
    "limit": {
      "default": 20,
      "description": "optional page size from 1 to 100; defaults to 20",
      "maximum": 100,
      "minimum": 1,
      "type": "integer"
    },
    "project_id": {
      "description": "optional returned project handle; omit for all runs including unassigned runs",
      "maxLength": 128,
      "minLength": 1,
      "type": [
        "null",
        "string"
      ]
    },
    "state": {
      "description": "optional queued, running, cancelling, succeeded, failed or cancelled filter; omit for all states",
      "enum": [
        "queued",
        "running",
        "cancelling",
        "succeeded",
        "failed",
        "cancelled"
      ],
      "type": "string"
    }
  },
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "next_cursor": {
      "type": "string"
    },
    "runs": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "created_at": {
            "type": "string"
          },
          "finished_at": {
            "type": [
              "null",
              "string"
            ]
          },
          "model_options": {
            "additionalProperties": false,
            "properties": {
              "all_sizes": {
                "type": "boolean"
              }
            },
            "required": [
              "all_sizes"
            ],
            "type": [
              "null",
              "object"
            ]
          },
          "next_action": {
            "additionalProperties": false,
            "properties": {
              "action": {
                "enum": [
                  "template",
                  "create",
                  "finalize",
                  "status"
                ],
                "type": "string"
              },
              "model_id": {
                "type": "string"
              },
              "prep_id": {
                "type": "string"
              },
              "run_id": {
                "type": "string"
              },
              "tool": {
                "enum": [
                  "prep_run",
                  "submit_run",
                  "get_results",
                  "get_model"
                ],
                "type": "string"
              },
              "use_new_key": {
                "type": "boolean"
              },
              "wait_seconds": {
                "default": 0,
                "maximum": 25,
                "minimum": 0,
                "type": "integer"
              }
            },
            "required": [
              "tool"
            ],
            "type": "object"
          },
          "prep_id": {
            "type": "string"
          },
          "project": {
            "additionalProperties": false,
            "properties": {
              "created_at": {
                "type": "string"
              },
              "name": {
                "type": "string"
              },
              "project_id": {
                "type": "string"
              },
              "updated_at": {
                "type": "string"
              }
            },
            "required": [
              "project_id",
              "name",
              "created_at",
              "updated_at"
            ],
            "type": [
              "null",
              "object"
            ]
          },
          "run_id": {
            "type": "string"
          },
          "run_name": {
            "type": "string"
          },
          "started_at": {
            "type": [
              "null",
              "string"
            ]
          },
          "state": {
            "enum": [
              "queued",
              "running",
              "cancelling",
              "succeeded",
              "failed",
              "cancelled"
            ],
            "type": "string"
          },
          "training_mode": {
            "enum": [
              "instant",
              "fast",
              "standard",
              "high",
              "ultra"
            ],
            "type": "string"
          },
          "updated_at": {
            "type": "string"
          }
        },
        "required": [
          "project",
          "run_name",
          "run_id",
          "prep_id",
          "state",
          "training_mode",
          "next_action",
          "created_at",
          "updated_at"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    }
  },
  "required": [
    "runs"
  ],
  "type": "object"
}
```


### list_skills

Read the default training guide for the workflow. Read define-prediction for unresolved target/output, label-definition or consequential input-scope choices. Read training-data for label coverage/assistance, or before combining sources or changing nulls, duplicates, conflicting labels, types or derived inputs. Guides are versioned; static reads do not verify account access. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "skills": {
      "description": "available server-versioned guides",
      "items": {
        "additionalProperties": false,
        "properties": {
          "name": {
            "description": "stable skill name",
            "type": "string"
          },
          "summary": {
            "description": "brief purpose of the guide",
            "type": "string"
          },
          "updated_at": {
            "description": "guide update date in YYYY-MM-DD format",
            "type": "string"
          },
          "version": {
            "description": "semantic version plus the first eight hex digits of the markdown SHA-256",
            "type": "string"
          }
        },
        "required": [
          "name",
          "version",
          "updated_at",
          "summary"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    }
  },
  "required": [
    "skills"
  ],
  "type": "object"
}
```


### prep_run

Pin one flat table and its prediction declaration. Call get_capabilities first: when it lists explicit tasks (formats: csv), supply prediction.task with a CSV, measured content_length and SHA-256 content_digest prefixed sha256:; validation runs in the training worker. Otherwise omit task to use the inferred route (CSV, Parquet, JSON, JSONL or ZIP; binary, multiclass, regression, or zero-label assistance when offered). Use action="template" for declaration examples matching the current capabilities, without creating an upload. For action="create", supply the actual file format and measured byte count, the completed prediction declaration and idempotency_key. Upload the file to the returned capability, then call action="finalize" with that prep_id; use action="status" to resume. Explicit ordinal requires a typed order; multilabel requires target_columns; ranking requires group_column and optional candidate_column, excluded from inputs. Preserve supplied labels and unlabelled examples. Returns actionable issues, or a ready receipt (csv_receipt for explicit tasks) with offered modes. Follow recorded next actions. Does not start training. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "oneOf": [
    {
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "template"
        }
      },
      "required": [
        "action"
      ],
      "type": "object"
    },
    {
      "additionalProperties": false,
      "allOf": [
        {
          "if": {
            "properties": {
              "prediction": {
                "required": [
                  "task"
                ]
              }
            },
            "required": [
              "prediction"
            ]
          },
          "then": {
            "properties": {
              "file": {
                "properties": {
                  "format": {
                    "const": "csv"
                  }
                },
                "required": [
                  "content_digest"
                ]
              }
            }
          }
        }
      ],
      "properties": {
        "action": {
          "const": "create"
        },
        "file": {
          "additionalProperties": false,
          "description": "create only: actual format and measured byte count of the final flat labelled table",
          "properties": {
            "content_digest": {
              "description": "SHA-256 of exact CSV bytes, prefixed sha256:, required for an explicit task",
              "pattern": "^sha256:[a-f0-9]{64}$",
              "type": "string"
            },
            "content_length": {
              "description": "exact positive byte count measured after local preparation",
              "minimum": 1,
              "type": "integer"
            },
            "format": {
              "description": "actual file format: parquet, csv, json, jsonl or zip; ZIP must resolve to one usable flat table",
              "enum": [
                "parquet",
                "csv",
                "json",
                "jsonl",
                "zip"
              ],
              "type": "string"
            }
          },
          "required": [
            "format",
            "content_length"
          ],
          "type": "object"
        },
        "idempotency_key": {
          "description": "caller-generated retry key: 1-255 characters of letters, digits, '.', '_', ':' or '-'; reuse it only to retry the identical request",
          "examples": [
            "forecast-upload-2026-09-24-01"
          ],
          "maxLength": 255,
          "minLength": 1,
          "pattern": "^[A-Za-z0-9._:-]{1,255}$",
          "type": "string"
        },
        "prediction": {
          "additionalProperties": false,
          "allOf": [
            {
              "else": {
                "not": {
                  "required": [
                    "positive_label"
                  ]
                }
              },
              "if": {
                "properties": {
                  "output_kind": {
                    "const": "event_probability"
                  }
                },
                "required": [
                  "output_kind"
                ]
              },
              "then": {
                "required": [
                  "positive_label"
                ]
              }
            }
          ],
          "description": "create only: one intended target and ordered inputs; physical column types are inferred",
          "oneOf": [
            {
              "not": {
                "required": [
                  "target_columns"
                ]
              },
              "required": [
                "target_column"
              ]
            },
            {
              "not": {
                "required": [
                  "target_column"
                ]
              },
              "properties": {
                "task": {
                  "const": "multilabel"
                }
              },
              "required": [
                "task",
                "target_columns"
              ]
            }
          ],
          "properties": {
            "candidate_column": {
              "description": "ranking only: optional unique candidate ID within each group, excluded from predictors",
              "type": "string"
            },
            "column_types": {
              "additionalProperties": false,
              "description": "explicit CSV task only, optional: input columns to read as embedding columns, each mapped to vector. Cells holding one JSON array of numbers or base64 float32 per row are detected without this. Not available with labeling",
              "maxProperties": 2048,
              "patternProperties": {
                "^": {
                  "enum": [
                    "vector"
                  ],
                  "type": "string"
                }
              },
              "propertyNames": {
                "maxLength": 255,
                "minLength": 1,
                "type": "string"
              },
              "type": "object"
            },
            "count_target": {
              "description": "count only: auto, raw, log1p or log1p_qmean",
              "enum": [
                "auto",
                "raw",
                "log1p",
                "log1p_qmean"
              ],
              "type": "string"
            },
            "group_column": {
              "description": "ranking only: required group column, excluded from predictors",
              "type": "string"
            },
            "input_columns": {
              "description": "ordered nonempty unique existing columns available at prediction time; exclude the target",
              "items": {
                "minLength": 1,
                "type": "string"
              },
              "minItems": 1,
              "type": "array",
              "uniqueItems": true
            },
            "labeling": {
              "additionalProperties": false,
              "description": "zero supplied labels only: required prediction description and complete typed outcome classes; optional unclear selected column meanings and already-known outcome shares; automatic server counts select the route, never a provider choice",
              "properties": {
                "classes": {
                  "items": {
                    "additionalProperties": false,
                    "properties": {
                      "meaning": {
                        "maxLength": 1000,
                        "type": "string"
                      },
                      "value": {
                        "oneOf": [
                          {
                            "type": "string"
                          },
                          {
                            "type": "boolean"
                          },
                          {
                            "type": "number"
                          }
                        ]
                      }
                    },
                    "required": [
                      "value"
                    ],
                    "type": "object"
                  },
                  "maxItems": 256,
                  "minItems": 2,
                  "type": [
                    "null",
                    "array"
                  ]
                },
                "columns": {
                  "additionalProperties": false,
                  "maxProperties": 2048,
                  "patternProperties": {
                    "^": {
                      "maxLength": 1000,
                      "minLength": 1,
                      "type": "string"
                    }
                  },
                  "propertyNames": {
                    "maxLength": 255,
                    "minLength": 1,
                    "type": "string"
                  },
                  "type": "object"
                },
                "description": {
                  "maxLength": 4000,
                  "minLength": 1,
                  "type": "string"
                },
                "outcome_shares": {
                  "additionalProperties": false,
                  "maxProperties": 256,
                  "patternProperties": {
                    "^": {
                      "exclusiveMaximum": 1,
                      "exclusiveMinimum": 0,
                      "type": "number"
                    }
                  },
                  "propertyNames": {
                    "maxLength": 8192,
                    "minLength": 1,
                    "type": "string"
                  },
                  "type": "object"
                }
              },
              "required": [
                "description",
                "classes"
              ],
              "type": [
                "null",
                "object"
              ]
            },
            "order": {
              "description": "ordinal only: ordered homogeneous original typed class domain",
              "items": {
                "additionalProperties": false,
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "value": {
                    "oneOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "boolean"
                      },
                      {
                        "type": "number"
                      }
                    ]
                  }
                },
                "required": [
                  "type",
                  "value"
                ],
                "type": "object"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "output_kind": {
              "description": "class_label for binary/multiclass; event_probability for binary; numeric_value for explicit regression",
              "enum": [
                "class_label",
                "event_probability",
                "numeric_value",
                "ordered_class",
                "count_value",
                "label_set",
                "ranking_score"
              ],
              "type": "string"
            },
            "pairs": {
              "description": "explicit CSV task only, optional: embedding pairs, each two different embedding input columns such as [query, title]; predictions send both sides. Not available with labeling",
              "items": {
                "items": {
                  "maxLength": 255,
                  "minLength": 1,
                  "type": "string"
                },
                "maxItems": 2,
                "minItems": 2,
                "type": "array"
              },
              "maxItems": 16,
              "type": "array"
            },
            "positive_label": {
              "description": "required only for event_probability; the observed event value as a JSON boolean or number, or its text as written in the file. Explicit-task CSV matches Oracle's canonical class key: numbers by value, true/false in any case, text with surrounding spaces ignored. For inferred declarations, keep the observed scalar type.",
              "oneOf": [
                {
                  "type": "string"
                },
                {
                  "type": "boolean"
                },
                {
                  "type": "number"
                }
              ]
            },
            "target_column": {
              "description": "one exact target column, present with empty/null cells when labels are absent; a string, never a list of targets",
              "minLength": 1,
              "type": "string"
            },
            "target_columns": {
              "description": "multilabel only: ordered independent binary target columns; omit target_column",
              "items": {
                "type": "string"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "task": {
              "description": "explicit CSV task: binary, multiclass, regression, ordinal, count, multilabel or ranking",
              "enum": [
                "binary",
                "multiclass",
                "regression",
                "ordinal",
                "count",
                "multilabel",
                "ranking"
              ],
              "type": "string"
            }
          },
          "required": [
            "input_columns",
            "output_kind"
          ],
          "type": "object"
        }
      },
      "required": [
        "action",
        "file",
        "prediction",
        "idempotency_key"
      ],
      "type": "object"
    },
    {
      "additionalProperties": false,
      "properties": {
        "action": {
          "enum": [
            "finalize",
            "status"
          ]
        },
        "prep_id": {
          "description": "finalize/status only: exact preparation UUID returned by 19th",
          "maxLength": 128,
          "minLength": 1,
          "type": "string"
        },
        "wait_seconds": {
          "description": "finalize/status only: 0 to 25 seconds; zero or absent returns immediately; a timeout leaves preparation running",
          "maximum": 25,
          "minimum": 0,
          "type": "integer"
        }
      },
      "required": [
        "action",
        "prep_id"
      ],
      "type": "object"
    }
  ],
  "properties": {
    "action": {
      "description": "template, create, finalize or status; template accepts only action and creates no upload",
      "enum": [
        "template",
        "create",
        "finalize",
        "status"
      ],
      "type": "string"
    },
    "file": {
      "additionalProperties": false,
      "description": "create only: actual format and measured byte count of the final flat labelled table",
      "properties": {
        "content_digest": {
          "description": "SHA-256 of exact CSV bytes, prefixed sha256:, required for an explicit task",
          "pattern": "^sha256:[a-f0-9]{64}$",
          "type": "string"
        },
        "content_length": {
          "description": "exact positive byte count measured after local preparation",
          "minimum": 1,
          "type": "integer"
        },
        "format": {
          "description": "actual file format: parquet, csv, json, jsonl or zip; ZIP must resolve to one usable flat table",
          "enum": [
            "parquet",
            "csv",
            "json",
            "jsonl",
            "zip"
          ],
          "type": "string"
        }
      },
      "required": [
        "format",
        "content_length"
      ],
      "type": "object"
    },
    "idempotency_key": {
      "description": "caller-generated retry key: 1-255 characters of letters, digits, '.', '_', ':' or '-'; reuse it only to retry the identical request",
      "examples": [
        "forecast-upload-2026-09-24-01"
      ],
      "maxLength": 255,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9._:-]{1,255}$",
      "type": "string"
    },
    "prediction": {
      "additionalProperties": false,
      "allOf": [
        {
          "else": {
            "not": {
              "required": [
                "positive_label"
              ]
            }
          },
          "if": {
            "properties": {
              "output_kind": {
                "const": "event_probability"
              }
            },
            "required": [
              "output_kind"
            ]
          },
          "then": {
            "required": [
              "positive_label"
            ]
          }
        }
      ],
      "description": "create only: one intended target and ordered inputs; physical column types are inferred",
      "oneOf": [
        {
          "not": {
            "required": [
              "target_columns"
            ]
          },
          "required": [
            "target_column"
          ]
        },
        {
          "not": {
            "required": [
              "target_column"
            ]
          },
          "properties": {
            "task": {
              "const": "multilabel"
            }
          },
          "required": [
            "task",
            "target_columns"
          ]
        }
      ],
      "properties": {
        "candidate_column": {
          "description": "ranking only: optional unique candidate ID within each group, excluded from predictors",
          "type": "string"
        },
        "column_types": {
          "additionalProperties": false,
          "description": "explicit CSV task only, optional: input columns to read as embedding columns, each mapped to vector. Cells holding one JSON array of numbers or base64 float32 per row are detected without this. Not available with labeling",
          "maxProperties": 2048,
          "patternProperties": {
            "^": {
              "enum": [
                "vector"
              ],
              "type": "string"
            }
          },
          "propertyNames": {
            "maxLength": 255,
            "minLength": 1,
            "type": "string"
          },
          "type": "object"
        },
        "count_target": {
          "description": "count only: auto, raw, log1p or log1p_qmean",
          "enum": [
            "auto",
            "raw",
            "log1p",
            "log1p_qmean"
          ],
          "type": "string"
        },
        "group_column": {
          "description": "ranking only: required group column, excluded from predictors",
          "type": "string"
        },
        "input_columns": {
          "description": "ordered nonempty unique existing columns available at prediction time; exclude the target",
          "items": {
            "minLength": 1,
            "type": "string"
          },
          "minItems": 1,
          "type": "array",
          "uniqueItems": true
        },
        "labeling": {
          "additionalProperties": false,
          "description": "zero supplied labels only: required prediction description and complete typed outcome classes; optional unclear selected column meanings and already-known outcome shares; automatic server counts select the route, never a provider choice",
          "properties": {
            "classes": {
              "items": {
                "additionalProperties": false,
                "properties": {
                  "meaning": {
                    "maxLength": 1000,
                    "type": "string"
                  },
                  "value": {
                    "oneOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "boolean"
                      },
                      {
                        "type": "number"
                      }
                    ]
                  }
                },
                "required": [
                  "value"
                ],
                "type": "object"
              },
              "maxItems": 256,
              "minItems": 2,
              "type": [
                "null",
                "array"
              ]
            },
            "columns": {
              "additionalProperties": false,
              "maxProperties": 2048,
              "patternProperties": {
                "^": {
                  "maxLength": 1000,
                  "minLength": 1,
                  "type": "string"
                }
              },
              "propertyNames": {
                "maxLength": 255,
                "minLength": 1,
                "type": "string"
              },
              "type": "object"
            },
            "description": {
              "maxLength": 4000,
              "minLength": 1,
              "type": "string"
            },
            "outcome_shares": {
              "additionalProperties": false,
              "maxProperties": 256,
              "patternProperties": {
                "^": {
                  "exclusiveMaximum": 1,
                  "exclusiveMinimum": 0,
                  "type": "number"
                }
              },
              "propertyNames": {
                "maxLength": 8192,
                "minLength": 1,
                "type": "string"
              },
              "type": "object"
            }
          },
          "required": [
            "description",
            "classes"
          ],
          "type": [
            "null",
            "object"
          ]
        },
        "order": {
          "description": "ordinal only: ordered homogeneous original typed class domain",
          "items": {
            "additionalProperties": false,
            "properties": {
              "type": {
                "type": "string"
              },
              "value": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "boolean"
                  },
                  {
                    "type": "number"
                  }
                ]
              }
            },
            "required": [
              "type",
              "value"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "output_kind": {
          "description": "class_label for binary/multiclass; event_probability for binary; numeric_value for explicit regression",
          "enum": [
            "class_label",
            "event_probability",
            "numeric_value",
            "ordered_class",
            "count_value",
            "label_set",
            "ranking_score"
          ],
          "type": "string"
        },
        "pairs": {
          "description": "explicit CSV task only, optional: embedding pairs, each two different embedding input columns such as [query, title]; predictions send both sides. Not available with labeling",
          "items": {
            "items": {
              "maxLength": 255,
              "minLength": 1,
              "type": "string"
            },
            "maxItems": 2,
            "minItems": 2,
            "type": "array"
          },
          "maxItems": 16,
          "type": "array"
        },
        "positive_label": {
          "description": "required only for event_probability; the observed event value as a JSON boolean or number, or its text as written in the file. Explicit-task CSV matches Oracle's canonical class key: numbers by value, true/false in any case, text with surrounding spaces ignored. For inferred declarations, keep the observed scalar type.",
          "oneOf": [
            {
              "type": "string"
            },
            {
              "type": "boolean"
            },
            {
              "type": "number"
            }
          ]
        },
        "target_column": {
          "description": "one exact target column, present with empty/null cells when labels are absent; a string, never a list of targets",
          "minLength": 1,
          "type": "string"
        },
        "target_columns": {
          "description": "multilabel only: ordered independent binary target columns; omit target_column",
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "task": {
          "description": "explicit CSV task: binary, multiclass, regression, ordinal, count, multilabel or ranking",
          "enum": [
            "binary",
            "multiclass",
            "regression",
            "ordinal",
            "count",
            "multilabel",
            "ranking"
          ],
          "type": "string"
        }
      },
      "required": [
        "input_columns",
        "output_kind"
      ],
      "type": "object"
    },
    "prep_id": {
      "description": "finalize/status only: exact preparation UUID returned by 19th",
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    },
    "wait_seconds": {
      "description": "finalize/status only: 0 to 25 seconds; zero or absent returns immediately; a timeout leaves preparation running",
      "maximum": 25,
      "minimum": 0,
      "type": "integer"
    }
  },
  "required": [
    "action"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "csv_receipt": {
      "additionalProperties": false,
      "properties": {
        "capability_version": {
          "type": "string"
        },
        "dataset_id": {
          "type": "string"
        },
        "dataset_version_id": {
          "type": "string"
        },
        "declaration_digest": {
          "type": "string"
        },
        "input_bytes": {
          "type": "integer"
        },
        "input_digest": {
          "type": "string"
        },
        "intake_declaration_digest": {
          "type": "string"
        },
        "offered_modes": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "prediction": {
          "additionalProperties": false,
          "properties": {
            "candidate_column": {
              "type": "string"
            },
            "column_types": {
              "additionalProperties": false,
              "maxProperties": 2048,
              "patternProperties": {
                "^": {
                  "enum": [
                    "vector"
                  ],
                  "type": "string"
                }
              },
              "propertyNames": {
                "maxLength": 255,
                "minLength": 1,
                "type": "string"
              },
              "type": "object"
            },
            "count_target": {
              "type": "string"
            },
            "group_column": {
              "type": "string"
            },
            "input_columns": {
              "items": {
                "type": "string"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "labeling": {
              "additionalProperties": false,
              "properties": {
                "classes": {
                  "items": {
                    "additionalProperties": false,
                    "properties": {
                      "meaning": {
                        "maxLength": 1000,
                        "type": "string"
                      },
                      "value": {
                        "oneOf": [
                          {
                            "type": "string"
                          },
                          {
                            "type": "boolean"
                          },
                          {
                            "type": "number"
                          }
                        ]
                      }
                    },
                    "required": [
                      "value"
                    ],
                    "type": "object"
                  },
                  "maxItems": 256,
                  "minItems": 2,
                  "type": [
                    "null",
                    "array"
                  ]
                },
                "columns": {
                  "additionalProperties": false,
                  "maxProperties": 2048,
                  "patternProperties": {
                    "^": {
                      "maxLength": 1000,
                      "minLength": 1,
                      "type": "string"
                    }
                  },
                  "propertyNames": {
                    "maxLength": 255,
                    "minLength": 1,
                    "type": "string"
                  },
                  "type": "object"
                },
                "description": {
                  "maxLength": 4000,
                  "minLength": 1,
                  "type": "string"
                },
                "outcome_shares": {
                  "additionalProperties": false,
                  "maxProperties": 256,
                  "patternProperties": {
                    "^": {
                      "exclusiveMaximum": 1,
                      "exclusiveMinimum": 0,
                      "type": "number"
                    }
                  },
                  "propertyNames": {
                    "maxLength": 8192,
                    "minLength": 1,
                    "type": "string"
                  },
                  "type": "object"
                }
              },
              "required": [
                "description",
                "classes"
              ],
              "type": [
                "null",
                "object"
              ]
            },
            "order": {
              "items": {
                "additionalProperties": false,
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "value": {
                    "oneOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "boolean"
                      },
                      {
                        "type": "number"
                      }
                    ]
                  }
                },
                "required": [
                  "type",
                  "value"
                ],
                "type": "object"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "output_kind": {
              "enum": [
                "class_label",
                "event_probability",
                "numeric_value",
                "ordered_class",
                "count_value",
                "label_set",
                "ranking_score"
              ],
              "type": "string"
            },
            "pairs": {
              "items": {
                "items": {
                  "type": "string"
                },
                "type": [
                  "null",
                  "array"
                ]
              },
              "type": [
                "null",
                "array"
              ]
            },
            "positive_label": {
              "additionalProperties": false,
              "properties": {
                "type": {
                  "type": "string"
                },
                "value": {
                  "oneOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "boolean"
                    },
                    {
                      "type": "number"
                    }
                  ]
                }
              },
              "required": [
                "type",
                "value"
              ],
              "type": [
                "null",
                "object"
              ]
            },
            "target_columns": {
              "items": {
                "type": "string"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "task": {
              "type": "string"
            }
          },
          "required": [
            "task",
            "input_columns",
            "target_columns",
            "output_kind"
          ],
          "type": "object"
        },
        "recipe_version": {
          "type": "string"
        },
        "schema_version": {
          "type": "string"
        },
        "source_generation": {
          "type": "string"
        },
        "source_storage_digest": {
          "type": "string"
        },
        "standard_all_sizes": {
          "type": "boolean"
        }
      },
      "required": [
        "schema_version",
        "dataset_id",
        "dataset_version_id",
        "source_storage_digest",
        "source_generation",
        "input_digest",
        "input_bytes",
        "prediction",
        "recipe_version",
        "capability_version",
        "declaration_digest",
        "offered_modes",
        "standard_all_sizes"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "expires_at": {
      "type": [
        "null",
        "string"
      ]
    },
    "formats": {
      "items": {
        "type": "string"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "hint": {
      "type": "string"
    },
    "issues": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "code": {
            "type": "string"
          },
          "column": {
            "type": "string"
          },
          "count": {
            "type": [
              "null",
              "integer"
            ]
          },
          "field": {
            "type": "string"
          },
          "hint": {
            "type": "string"
          },
          "message": {
            "type": "string"
          }
        },
        "required": [
          "field",
          "code",
          "message",
          "hint"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "next_action": {
      "additionalProperties": false,
      "properties": {
        "action": {
          "enum": [
            "template",
            "create",
            "finalize",
            "status"
          ],
          "type": "string"
        },
        "model_id": {
          "type": "string"
        },
        "prep_id": {
          "type": "string"
        },
        "run_id": {
          "type": "string"
        },
        "tool": {
          "enum": [
            "prep_run",
            "submit_run",
            "get_results",
            "get_model"
          ],
          "type": "string"
        },
        "use_new_key": {
          "type": "boolean"
        },
        "wait_seconds": {
          "default": 0,
          "maximum": 25,
          "minimum": 0,
          "type": "integer"
        }
      },
      "required": [
        "tool"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "prep_id": {
      "type": "string"
    },
    "receipt": {
      "additionalProperties": false,
      "properties": {
        "capability_version": {
          "type": "string"
        },
        "classes": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "canonical": {
                "type": "string"
              },
              "index": {
                "type": "integer"
              },
              "label": {
                "additionalProperties": false,
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "value": {
                    "oneOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "boolean"
                      },
                      {
                        "type": "number"
                      }
                    ]
                  }
                },
                "required": [
                  "type",
                  "value"
                ],
                "type": "object"
              }
            },
            "required": [
              "index",
              "canonical",
              "label"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "dataset_id": {
          "type": "string"
        },
        "dataset_version_id": {
          "type": "string"
        },
        "declaration_digest": {
          "type": "string"
        },
        "effective_inputs": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "dimension": {
                "maximum": 4096,
                "minimum": 1,
                "type": "integer"
              },
              "encoder": {
                "additionalProperties": false,
                "properties": {
                  "instruction": {
                    "type": "string"
                  },
                  "name": {
                    "type": "string"
                  },
                  "revision": {
                    "type": "string"
                  }
                },
                "type": "object"
              },
              "formats": {
                "items": {
                  "type": "string"
                },
                "type": [
                  "null",
                  "array"
                ]
              },
              "kind": {
                "type": "string"
              },
              "name": {
                "type": "string"
              },
              "parts": {
                "items": {
                  "type": "string"
                },
                "type": [
                  "null",
                  "array"
                ]
              }
            },
            "required": [
              "name",
              "kind"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "evaluation": {
          "additionalProperties": false,
          "properties": {
            "assumptions": {
              "items": {
                "type": "string"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "method": {
              "type": "string"
            },
            "policy_version": {
              "type": "string"
            }
          },
          "required": [
            "policy_version",
            "method",
            "assumptions"
          ],
          "type": "object"
        },
        "excluded_inputs": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "column": {
                "type": "string"
              },
              "reason": {
                "type": "string"
              }
            },
            "required": [
              "column",
              "reason"
            ],
            "type": "object"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "inference_runtime": {
          "additionalProperties": false,
          "properties": {
            "numpy": {
              "type": "string"
            },
            "pandas": {
              "type": "string"
            },
            "pyarrow": {
              "type": "string"
            },
            "python": {
              "type": "string"
            }
          },
          "required": [
            "python",
            "numpy",
            "pandas",
            "pyarrow"
          ],
          "type": "object"
        },
        "inference_version": {
          "type": "string"
        },
        "label_coverage": {
          "additionalProperties": false,
          "properties": {
            "labeled": {
              "type": "integer"
            },
            "unlabeled": {
              "type": "integer"
            }
          },
          "required": [
            "labeled",
            "unlabeled"
          ],
          "type": [
            "null",
            "object"
          ]
        },
        "offered_modes": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "positive_class_index": {
          "type": [
            "null",
            "integer"
          ]
        },
        "prediction": {
          "additionalProperties": false,
          "properties": {
            "candidate_column": {
              "type": "string"
            },
            "column_types": {
              "additionalProperties": false,
              "maxProperties": 2048,
              "patternProperties": {
                "^": {
                  "enum": [
                    "vector"
                  ],
                  "type": "string"
                }
              },
              "propertyNames": {
                "maxLength": 255,
                "minLength": 1,
                "type": "string"
              },
              "type": "object"
            },
            "count_target": {
              "type": "string"
            },
            "group_column": {
              "type": "string"
            },
            "input_columns": {
              "items": {
                "type": "string"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "labeling": {
              "additionalProperties": false,
              "properties": {
                "classes": {
                  "items": {
                    "additionalProperties": false,
                    "properties": {
                      "meaning": {
                        "maxLength": 1000,
                        "type": "string"
                      },
                      "value": {
                        "oneOf": [
                          {
                            "type": "string"
                          },
                          {
                            "type": "boolean"
                          },
                          {
                            "type": "number"
                          }
                        ]
                      }
                    },
                    "required": [
                      "value"
                    ],
                    "type": "object"
                  },
                  "maxItems": 256,
                  "minItems": 2,
                  "type": [
                    "null",
                    "array"
                  ]
                },
                "columns": {
                  "additionalProperties": false,
                  "maxProperties": 2048,
                  "patternProperties": {
                    "^": {
                      "maxLength": 1000,
                      "minLength": 1,
                      "type": "string"
                    }
                  },
                  "propertyNames": {
                    "maxLength": 255,
                    "minLength": 1,
                    "type": "string"
                  },
                  "type": "object"
                },
                "description": {
                  "maxLength": 4000,
                  "minLength": 1,
                  "type": "string"
                },
                "outcome_shares": {
                  "additionalProperties": false,
                  "maxProperties": 256,
                  "patternProperties": {
                    "^": {
                      "exclusiveMaximum": 1,
                      "exclusiveMinimum": 0,
                      "type": "number"
                    }
                  },
                  "propertyNames": {
                    "maxLength": 8192,
                    "minLength": 1,
                    "type": "string"
                  },
                  "type": "object"
                }
              },
              "required": [
                "description",
                "classes"
              ],
              "type": [
                "null",
                "object"
              ]
            },
            "order": {
              "items": {
                "additionalProperties": false,
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "value": {
                    "oneOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "boolean"
                      },
                      {
                        "type": "number"
                      }
                    ]
                  }
                },
                "required": [
                  "type",
                  "value"
                ],
                "type": "object"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "output_kind": {
              "enum": [
                "class_label",
                "event_probability",
                "numeric_value",
                "ordered_class",
                "count_value",
                "label_set",
                "ranking_score"
              ],
              "type": "string"
            },
            "pairs": {
              "items": {
                "items": {
                  "type": "string"
                },
                "type": [
                  "null",
                  "array"
                ]
              },
              "type": [
                "null",
                "array"
              ]
            },
            "positive_label": {
              "oneOf": [
                {
                  "type": "string"
                },
                {
                  "type": "boolean"
                },
                {
                  "type": "number"
                }
              ]
            },
            "target_column": {
              "type": "string"
            },
            "target_columns": {
              "items": {
                "type": "string"
              },
              "type": [
                "null",
                "array"
              ]
            },
            "task": {
              "type": "string"
            }
          },
          "required": [
            "input_columns",
            "output_kind"
          ],
          "type": "object"
        },
        "prepared_digest": {
          "type": "string"
        },
        "prepared_receipt_digest": {
          "type": "string"
        },
        "recipe_version": {
          "type": "string"
        },
        "row_count": {
          "type": "integer"
        },
        "schema_version": {
          "type": "string"
        },
        "source_digest": {
          "type": "string"
        },
        "source_generation": {
          "type": "string"
        },
        "standard_all_sizes": {
          "type": "boolean"
        },
        "task_kind": {
          "enum": [
            "binary",
            "multiclass",
            "regression",
            "ordinal",
            "count",
            "multilabel",
            "ranking"
          ],
          "type": "string"
        },
        "validation_version": {
          "type": "string"
        },
        "warnings": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        }
      },
      "required": [
        "inference_runtime",
        "recipe_version",
        "capability_version",
        "declaration_digest",
        "schema_version",
        "validation_version",
        "inference_version",
        "dataset_id",
        "dataset_version_id",
        "source_digest",
        "source_generation",
        "prepared_digest",
        "prepared_receipt_digest",
        "prediction",
        "effective_inputs",
        "excluded_inputs",
        "task_kind",
        "row_count",
        "evaluation",
        "offered_modes",
        "standard_all_sizes",
        "warnings"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "retained_until": {
      "type": [
        "null",
        "string"
      ]
    },
    "state": {
      "enum": [
        "awaiting_upload",
        "preparing",
        "ready",
        "failed",
        "expired"
      ],
      "type": "string"
    },
    "templates": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "declaration": {
            "additionalProperties": false,
            "description": "fillable declaration; replace placeholders with inspected actual columns and exact observed event label type",
            "properties": {
              "candidate_column": {
                "description": "ranking only: optional unique candidate ID within each group, excluded from predictors",
                "type": "string"
              },
              "column_types": {
                "additionalProperties": false,
                "description": "explicit CSV task only, optional: input columns to read as embedding columns, each mapped to vector. Cells holding one JSON array of numbers or base64 float32 per row are detected without this. Not available with labeling",
                "maxProperties": 2048,
                "patternProperties": {
                  "^": {
                    "enum": [
                      "vector"
                    ],
                    "type": "string"
                  }
                },
                "propertyNames": {
                  "maxLength": 255,
                  "minLength": 1,
                  "type": "string"
                },
                "type": "object"
              },
              "count_target": {
                "description": "count only: auto, raw, log1p or log1p_qmean",
                "type": "string"
              },
              "group_column": {
                "description": "ranking only: required group column, excluded from predictors",
                "type": "string"
              },
              "input_columns": {
                "description": "ordered nonempty unique existing columns available at prediction time; exclude the target",
                "items": {
                  "type": "string"
                },
                "type": [
                  "null",
                  "array"
                ]
              },
              "labeling": {
                "additionalProperties": false,
                "description": "zero supplied labels only: required prediction description and complete typed outcome classes; optional unclear selected column meanings and already-known outcome shares; automatic server counts select the route, never a provider choice",
                "properties": {
                  "classes": {
                    "items": {
                      "additionalProperties": false,
                      "properties": {
                        "meaning": {
                          "maxLength": 1000,
                          "type": "string"
                        },
                        "value": {
                          "oneOf": [
                            {
                              "type": "string"
                            },
                            {
                              "type": "boolean"
                            },
                            {
                              "type": "number"
                            }
                          ]
                        }
                      },
                      "required": [
                        "value"
                      ],
                      "type": "object"
                    },
                    "maxItems": 256,
                    "minItems": 2,
                    "type": [
                      "null",
                      "array"
                    ]
                  },
                  "columns": {
                    "additionalProperties": false,
                    "maxProperties": 2048,
                    "patternProperties": {
                      "^": {
                        "maxLength": 1000,
                        "minLength": 1,
                        "type": "string"
                      }
                    },
                    "propertyNames": {
                      "maxLength": 255,
                      "minLength": 1,
                      "type": "string"
                    },
                    "type": "object"
                  },
                  "description": {
                    "maxLength": 4000,
                    "minLength": 1,
                    "type": "string"
                  },
                  "outcome_shares": {
                    "additionalProperties": false,
                    "maxProperties": 256,
                    "patternProperties": {
                      "^": {
                        "exclusiveMaximum": 1,
                        "exclusiveMinimum": 0,
                        "type": "number"
                      }
                    },
                    "propertyNames": {
                      "maxLength": 8192,
                      "minLength": 1,
                      "type": "string"
                    },
                    "type": "object"
                  }
                },
                "required": [
                  "description",
                  "classes"
                ],
                "type": [
                  "null",
                  "object"
                ]
              },
              "order": {
                "description": "ordinal only: ordered homogeneous original typed class domain",
                "items": {
                  "additionalProperties": false,
                  "properties": {
                    "type": {
                      "type": "string"
                    },
                    "value": {
                      "oneOf": [
                        {
                          "type": "string"
                        },
                        {
                          "type": "boolean"
                        },
                        {
                          "type": "number"
                        }
                      ]
                    }
                  },
                  "required": [
                    "type",
                    "value"
                  ],
                  "type": "object"
                },
                "type": [
                  "null",
                  "array"
                ]
              },
              "output_kind": {
                "description": "class_label for binary/multiclass; event_probability for binary; numeric_value for explicit regression",
                "enum": [
                  "class_label",
                  "event_probability",
                  "numeric_value",
                  "ordered_class",
                  "count_value",
                  "label_set",
                  "ranking_score"
                ],
                "type": "string"
              },
              "pairs": {
                "description": "explicit CSV task only, optional: embedding pairs, each two different embedding input columns such as [query, title]; predictions send both sides. Not available with labeling",
                "items": {
                  "items": {
                    "type": "string"
                  },
                  "type": [
                    "null",
                    "array"
                  ]
                },
                "type": [
                  "null",
                  "array"
                ]
              },
              "positive_label": {
                "description": "required only for event_probability; the observed event value as a JSON boolean or number, or its text as written in the file. Explicit-task CSV matches Oracle's canonical class key: numbers by value, true/false in any case, text with surrounding spaces ignored. For inferred declarations, keep the observed scalar type.",
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "boolean"
                  },
                  {
                    "type": "number"
                  }
                ]
              },
              "target_column": {
                "description": "one exact target column, present with empty/null cells when labels are absent; a string, never a list of targets",
                "type": "string"
              },
              "target_columns": {
                "description": "multilabel only: ordered independent binary target columns; omit target_column",
                "items": {
                  "type": "string"
                },
                "type": [
                  "null",
                  "array"
                ]
              },
              "task": {
                "description": "explicit CSV task: binary, multiclass, regression, ordinal, count, multilabel or ranking",
                "type": "string"
              }
            },
            "required": [
              "input_columns",
              "output_kind"
            ],
            "type": "object"
          },
          "output_kind": {
            "description": "requested public prediction output",
            "enum": [
              "class_label",
              "event_probability",
              "numeric_value",
              "ordered_class",
              "count_value",
              "label_set",
              "ranking_score"
            ],
            "type": "string"
          }
        },
        "required": [
          "output_kind",
          "declaration"
        ],
        "type": "object"
      },
      "type": [
        "null",
        "array"
      ]
    },
    "upload": {
      "additionalProperties": false,
      "properties": {
        "allowed_egress_hosts": {
          "items": {
            "type": "string"
          },
          "type": [
            "null",
            "array"
          ]
        },
        "expires_at": {
          "type": "string"
        },
        "headers": {
          "additionalProperties": {
            "type": "string"
          },
          "type": "object"
        },
        "method": {
          "type": "string"
        },
        "url": {
          "type": "string"
        }
      },
      "required": [
        "url",
        "method",
        "headers",
        "expires_at",
        "allowed_egress_hosts"
      ],
      "type": [
        "null",
        "object"
      ]
    }
  },
  "type": "object"
}
```


### request_download

Prepare an authorized model download selection. Supply run_id and select one or multiple model_ids from get_results, one format (tfpb by default), archive or raw delivery, and no, selected or all runtimes. For runtimes copy exact handles and catalog_version from get_download_options. Raw requires one model and no runtime. Repeat identical arguments after an uncertain response; returned download_id fixes model and runtime versions. Legacy models or unqualified runtimes can be unavailable. Call get_download to read status and obtain the transfer descriptor. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "catalog_version": {
      "description": "exact catalog_version returned by get_download_options; required with selected or all runtimes; preserve on retries",
      "type": "string"
    },
    "delivery": {
      "description": "archive by default; raw returns exactly one model file with no runtime",
      "enum": [
        "archive",
        "raw"
      ],
      "type": "string"
    },
    "format": {
      "description": "model file format; defaults to tfpb",
      "enum": [
        "tfpb",
        "npz"
      ],
      "type": "string"
    },
    "model_ids": {
      "description": "one or more exact model_id handles returned by get_results",
      "items": {
        "maxLength": 2048,
        "minLength": 1,
        "type": "string"
      },
      "maxItems": 64,
      "minItems": 1,
      "type": [
        "null",
        "array"
      ],
      "uniqueItems": true
    },
    "run_id": {
      "description": "exact run_id returned by get_results",
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    },
    "runtime": {
      "additionalProperties": false,
      "description": "none by default, selected exact runtime handles from get_download_options, or all newest qualified compatible SDK releases, one per concrete target",
      "properties": {
        "mode": {
          "enum": [
            "none",
            "selected",
            "all"
          ],
          "type": "string"
        },
        "targets": {
          "items": {
            "pattern": "^[a-z0-9][a-z0-9._-]{0,127}$",
            "type": "string"
          },
          "maxItems": 64,
          "minItems": 1,
          "type": [
            "null",
            "array"
          ],
          "uniqueItems": true
        }
      },
      "required": [
        "mode"
      ],
      "type": "object"
    }
  },
  "required": [
    "run_id",
    "model_ids"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "oneOf": [
    {
      "not": {
        "anyOf": [
          {
            "required": [
              "download"
            ]
          },
          {
            "required": [
              "failure_code"
            ]
          },
          {
            "required": [
              "retryable"
            ]
          }
        ]
      },
      "properties": {
        "state": {
          "const": "preparing"
        }
      }
    },
    {
      "not": {
        "required": [
          "download"
        ]
      },
      "properties": {
        "state": {
          "const": "failed"
        }
      },
      "required": [
        "failure_code",
        "retryable"
      ]
    },
    {
      "not": {
        "anyOf": [
          {
            "required": [
              "failure_code"
            ]
          },
          {
            "required": [
              "retryable"
            ]
          }
        ]
      },
      "properties": {
        "state": {
          "const": "ready"
        }
      }
    }
  ],
  "properties": {
    "download": {
      "additionalProperties": false,
      "properties": {
        "bytes": {
          "type": "integer"
        },
        "content_type": {
          "enum": [
            "application/zip",
            "application/octet-stream"
          ],
          "type": "string"
        },
        "expires_at": {
          "type": "string"
        },
        "filename": {
          "type": "string"
        },
        "method": {
          "enum": [
            "GET"
          ],
          "type": "string"
        },
        "sha256": {
          "pattern": "^[a-f0-9]{64}$",
          "type": "string"
        },
        "url": {
          "type": "string"
        }
      },
      "required": [
        "url",
        "method",
        "expires_at",
        "filename",
        "bytes",
        "sha256",
        "content_type"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "download_id": {
      "type": "string"
    },
    "failure_code": {
      "enum": [
        "DOWNLOAD_UNAVAILABLE",
        "DOWNLOAD_INVALID"
      ],
      "type": "string"
    },
    "retryable": {
      "type": [
        "null",
        "boolean"
      ]
    },
    "run_id": {
      "type": "string"
    },
    "schema_version": {
      "enum": [
        "model_download.v1"
      ],
      "type": "string"
    },
    "selection": {
      "additionalProperties": false,
      "properties": {
        "catalog_version": {
          "type": "string"
        },
        "delivery": {
          "enum": [
            "archive",
            "raw"
          ],
          "type": "string"
        },
        "format": {
          "enum": [
            "tfpb",
            "npz"
          ],
          "type": "string"
        },
        "model_ids": {
          "items": {
            "type": "string"
          },
          "maxItems": 64,
          "minItems": 1,
          "type": "array",
          "uniqueItems": true
        },
        "runtime": {
          "additionalProperties": false,
          "properties": {
            "mode": {
              "enum": [
                "none",
                "selected",
                "all"
              ],
              "type": "string"
            },
            "targets": {
              "items": {
                "type": "string"
              },
              "maxItems": 64,
              "minItems": 1,
              "type": "array",
              "uniqueItems": true
            }
          },
          "required": [
            "mode"
          ],
          "type": "object"
        }
      },
      "required": [
        "model_ids",
        "format",
        "delivery",
        "runtime"
      ],
      "type": "object"
    },
    "state": {
      "enum": [
        "preparing",
        "failed",
        "ready"
      ],
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "run_id",
    "download_id",
    "state",
    "selection"
  ],
  "type": "object"
}
```


### set_run_project

Assign an existing run to a project, move it to another project, or remove its project assignment. Supply run_id, project_id and idempotency_key; use project_id=null to remove the assignment. Returns the run's saved project assignment. This changes organization only, without restarting training or changing access. Retry an uncertain response with the same key and arguments. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "idempotency_key": {
      "description": "caller-generated retry key: 1-255 characters of letters, digits, '.', '_', ':' or '-'; reuse it only to retry the identical request",
      "examples": [
        "forecast-upload-2026-09-24-01"
      ],
      "maxLength": 255,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9._:-]{1,255}$",
      "type": "string"
    },
    "project_id": {
      "description": "project handle returned by list_projects or create_project; null removes the assignment",
      "format": "uuid",
      "type": [
        "string",
        "null"
      ]
    },
    "run_id": {
      "description": "run handle returned by submit_run or list_runs",
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "run_id",
    "project_id",
    "idempotency_key"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "project": {
      "additionalProperties": false,
      "properties": {
        "created_at": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "project_id": {
          "type": "string"
        },
        "updated_at": {
          "type": "string"
        }
      },
      "required": [
        "project_id",
        "name",
        "created_at",
        "updated_at"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "run_id": {
      "type": "string"
    }
  },
  "required": [
    "run_id",
    "project"
  ],
  "type": "object"
}
```


### submit_run

Start one training run from a ready preparation. Supply prep_id, run_name, training_mode from that preparation's offered modes, and a caller-generated idempotency_key. Current training offers instant, standard and high, plus ultra where offered; Fast is historical-only, for frozen older preparations or exact retries. Choose the training mode that best fits the user’s goal, using the supplied mode descriptions. If the user’s preference on these training trade-offs isn’t clear, briefly explain the relevant tradeoffs and ask what they prefer. Proceed when their instructions or existing context settle the choice. Use the returned model menu for downloads. Fast, Turbo and Warpspeed are output variants, independent of training effort. Omit model_options; its all_sizes setting was removed. The data and prediction declaration are already bound to prep_id; do not resend them or supply an image. Optionally supply a project_id returned by list_projects or create_project to group the run. Omit it to leave the run unassigned. This project groups runs within the connection's existing access. Returns run_id and current state. After an uncertain response, retry the same key and exact arguments to recover the same submission. Follow the default training-v2 guide from get_skill. Use this tool's input schema and field descriptions for required fields.

Input schema:

```json
{
  "additionalProperties": false,
  "allOf": [
    {
      "if": {
        "properties": {
          "model_options": true
        },
        "required": [
          "model_options"
        ]
      },
      "then": {
        "properties": {
          "training_mode": {
            "const": "standard"
          }
        }
      }
    }
  ],
  "properties": {
    "idempotency_key": {
      "description": "caller-generated retry key: 1-255 characters of letters, digits, '.', '_', ':' or '-'; reuse it only to retry the identical request",
      "examples": [
        "forecast-upload-2026-09-24-01"
      ],
      "maxLength": 255,
      "minLength": 1,
      "pattern": "^[A-Za-z0-9._:-]{1,255}$",
      "type": "string"
    },
    "model_options": {
      "additionalProperties": false,
      "description": "Removed: omit. Every run returns Fast, Turbo and Warpspeed",
      "properties": {
        "all_sizes": {
          "description": "Removed: omit model_options. true is refused because every run returns the same three downloads, Fast, Turbo and Warpspeed",
          "type": "boolean"
        }
      },
      "required": [
        "all_sizes"
      ],
      "type": "object"
    },
    "prep_id": {
      "description": "exact ready preparation UUID containing intended table, target, inputs and output",
      "maxLength": 128,
      "minLength": 1,
      "type": "string"
    },
    "project_id": {
      "description": "Optional project handle returned by list_projects or create_project for grouping this run; omit to leave it unassigned. This does not select a workspace or change access.",
      "maxLength": 128,
      "minLength": 1,
      "type": [
        "null",
        "string"
      ]
    },
    "run_name": {
      "description": "Short name for this run, based on the prediction goal. Use 2–7 words and at most 80 characters, in sentence case without trailing punctuation. Choose it yourself without asking the user.",
      "maxLength": 80,
      "minLength": 1,
      "type": "string"
    },
    "training_mode": {
      "description": "Choose from this preparation’s offered_modes and supplied descriptions. Current training offers instant, standard and high, plus ultra where offered. fast is historical-only, for frozen older preparations and exact retries",
      "enum": [
        "instant",
        "fast",
        "standard",
        "high",
        "ultra"
      ],
      "type": "string"
    }
  },
  "required": [
    "prep_id",
    "run_name",
    "training_mode",
    "idempotency_key"
  ],
  "type": "object"
}
```

Output schema:

```json
{
  "additionalProperties": false,
  "properties": {
    "model_options": {
      "additionalProperties": false,
      "properties": {
        "all_sizes": {
          "type": "boolean"
        }
      },
      "required": [
        "all_sizes"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "next_action": {
      "additionalProperties": false,
      "properties": {
        "action": {
          "enum": [
            "template",
            "create",
            "finalize",
            "status"
          ],
          "type": "string"
        },
        "model_id": {
          "type": "string"
        },
        "prep_id": {
          "type": "string"
        },
        "run_id": {
          "type": "string"
        },
        "tool": {
          "enum": [
            "prep_run",
            "submit_run",
            "get_results",
            "get_model"
          ],
          "type": "string"
        },
        "use_new_key": {
          "type": "boolean"
        },
        "wait_seconds": {
          "default": 0,
          "maximum": 25,
          "minimum": 0,
          "type": "integer"
        }
      },
      "required": [
        "tool"
      ],
      "type": "object"
    },
    "prep_id": {
      "type": "string"
    },
    "project": {
      "additionalProperties": false,
      "properties": {
        "created_at": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "project_id": {
          "type": "string"
        },
        "updated_at": {
          "type": "string"
        }
      },
      "required": [
        "project_id",
        "name",
        "created_at",
        "updated_at"
      ],
      "type": [
        "null",
        "object"
      ]
    },
    "run_id": {
      "type": "string"
    },
    "run_name": {
      "type": "string"
    },
    "state": {
      "enum": [
        "queued",
        "running",
        "cancelling",
        "succeeded",
        "failed",
        "cancelled"
      ],
      "type": "string"
    },
    "training_mode": {
      "enum": [
        "instant",
        "fast",
        "standard",
        "high",
        "ultra"
      ],
      "type": "string"
    }
  },
  "required": [
    "project",
    "run_name",
    "run_id",
    "prep_id",
    "state",
    "training_mode",
    "next_action"
  ],
  "type": "object"
}
```


## If setup needs troubleshooting

### The tools do not appear

Check the server URL, remote HTTP transport, and the client's MCP settings. Complete sign-in and refresh the client connection. Some clients require a new session before newly added tools appear.

### Sign-in works but access is refused

Read the error from `get_capabilities`. Check the selected account, invited email address and workspace access. Follow the [account access guidance](/docs#get-access) if you need help. Confirm access with `get_capabilities` before uploading or training.

### Preparation reports an issue

Follow the returned field issues and hints. Keep the target present, select existing input columns, and preserve scalar label types. Correct the table or declaration and prepare again only when the response requires a new preparation.

### Call times out

Resume reads with the same preparation or run handle. Retry a mutation with the same idempotency key and exact arguments. Do not resubmit with a fresh key merely because a response was lost.

### Download is still preparing

Follow its returned readiness and next action. Training completion does not guarantee that every bundle has already been assembled. Request a fresh link if a ready download's URL expires.

## Questions

### Do I need an API key to use MCP?

No. Sign in to your 19th account through your agent's connection settings. API keys are only needed when calling the Training or Inference API directly.

### What type of data do I need?

Bring a table of examples with the information you'll have when making a prediction. Include any known outcomes, such as whether a customer canceled or how long a delivery took.

If you're predicting a category or the chance of an outcome, 19th can help label your examples. Tell your agent what you want to predict and the possible answers. To predict a number, your examples need known outcomes to learn from.

### Can I run a model in my own application?

Yes. Once your model's download is ready, your agent can retrieve it and help you set it up with a compatible SDK. You can also get predictions through the [Inference API](/docs/inference); your agent can help you get the URL and API key. Hosted predictions must be ready before you can use them.

### Can I resume or stop a run?

You can leave and come back while training continues. Ask your agent to find the run and check its progress. To stop it, ask your agent to cancel it and confirm whether cancellation succeeded.

### Can my agent read this guide directly?

Yes. Share the [Markdown guide](/docs/mcp.md) with your agent.
