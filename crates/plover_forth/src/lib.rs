mod interpreter;

pub use interpreter::{Forth, ForthError, ForthScenarioResult};

pub fn run_forth_scenario_yaml(
    actions: &[serde_yaml::Value],
    expect: &serde_yaml::Value,
) -> ForthScenarioResult {
    let mut f = Forth::new(None);
    for action in actions {
        let typ = action.get("type").and_then(|v| v.as_str()).unwrap_or("");
        match typ {
            "eval" => {
                let line = action
                    .get("line")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                if let Err(e) = f.eval_line(line) {
                    return ForthScenarioResult {
                        ok: false,
                        output: f.output.clone(),
                        stack: f.data.clone(),
                        error: Some(e.to_string()),
                    };
                }
            }
            "reset" => f = Forth::new(None),
            other => {
                return ForthScenarioResult {
                    ok: false,
                    output: f.output.clone(),
                    stack: f.data.clone(),
                    error: Some(format!("unknown forth action: {other}")),
                };
            }
        }
    }
    let mut ok = true;
    if let serde_yaml::Value::Mapping(map) = expect {
        if let Some(stack) = map.get(&serde_yaml::Value::String("stack".into())) {
            if let serde_yaml::Value::Sequence(seq) = stack {
                let want: Vec<u16> = seq
                    .iter()
                    .filter_map(|v| v.as_i64().map(|i| i as u16))
                    .collect();
                if want != f.data {
                    ok = false;
                }
            }
        }
        if let Some(output) = map.get(&serde_yaml::Value::String("output".into())) {
            if let serde_yaml::Value::Sequence(seq) = output {
                let want: Vec<String> = seq
                    .iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect();
                if want != f.output {
                    ok = false;
                }
            }
        }
    }
    ForthScenarioResult {
        ok,
        output: f.output,
        stack: f.data,
        error: None,
    }
}
