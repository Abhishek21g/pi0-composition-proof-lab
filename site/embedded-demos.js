window.EMBEDDED_DEMOS = {
  "airfryer-receipt.json": {
    "run_id": "pi07-airfryer-demo",
    "task": "load a sweet potato into the air fryer",
    "verdict": "COACH_REQUIRED",
    "coaching_required": true,
    "skill_matches": [
      {
        "skill_id": "place_in_container",
        "episode_id": "home_airfryer_close_02",
        "score": 1.0,
        "instruction": "put the basket of the airfryer on the leftmost side of the counter",
        "robot": "mobile_manipulator"
      },
      {
        "skill_id": "close_container",
        "episode_id": "home_airfryer_close_01",
        "score": 1.0,
        "instruction": "push the frying basket into the airfryer",
        "robot": "mobile_manipulator"
      },
      {
        "skill_id": "operate_appliance",
        "episode_id": "home_airfryer_close_01",
        "score": 1.0,
        "instruction": "push the frying basket into the airfryer",
        "robot": "mobile_manipulator"
      },
      {
        "skill_id": "place_in_container",
        "episode_id": "droid_franka_pot_01",
        "score": 1.0,
        "instruction": "move the pot onto the stove",
        "robot": "franka"
      }
    ],
    "tangential_episodes": [
      "home_airfryer_close_02",
      "droid_franka_pot_01",
      "home_airfryer_close_01"
    ],
    "doctors": [
      {
        "name": "skill_graph",
        "passed": true,
        "score": 1.0,
        "detail": "3/3 task skills have manifest support"
      },
      {
        "name": "manifest_search",
        "passed": true,
        "score": 1.0,
        "detail": "9 skill→episode matches"
      },
      {
        "name": "remix_detector",
        "passed": false,
        "score": 1.0,
        "detail": "high remix means tangential training evidence dominates"
      },
      {
        "name": "embodiment_gap",
        "passed": true,
        "score": 0.0,
        "detail": "eval robot=mobile_manipulator"
      },
      {
        "name": "coaching_oracle",
        "passed": false,
        "score": 1.0,
        "detail": "step-by-step language coaching likely required"
      }
    ],
    "notes": [
      "Mirrors π0.7 blog postmortem: two air-fryer-close episodes + DROID Franka tangents",
      "Zero-shot prompt fails; step coaching succeeds — not deploy preflight"
    ]
  }
};
