# Material Graph: HLSL <-> Node Mapping Reference

Domain: `material_graph` (via `unreal_ue` router with `domain: "material"`)

## Operations

| Operation | Description | Required Params |
|-----------|-------------|-----------------|
| `get_graph_as_hlsl` | Pseudo-HLSL with GUID annotations | material_path |
| `get_compiled_hlsl` | Engine-compiled actual HLSL | material_path |
| `get_graph` | Full node JSON (pins, properties, GUIDs) | material_path |
| `get_graph_summary` | Quick overview (type counts, params, chains) | material_path |
| `add_expression` | Add a material expression node | material_path, expression_class |
| `connect` | Connect two node pins | material_path, source_guid, source_pin, dest_guid, dest_pin |
| `disconnect` | Break a pin connection | material_path, guid, pin_name |
| `delete_expression` | Remove a node | material_path, guid |
| `set_expression_property` | Set node property value | material_path, guid, property, value |
| `compile` | Recompile shader + auto-comment modified nodes | material_path |
| `list_expression_types` | List available expression classes | — |
| `add_comment` | Add comment node around expressions | material_path, text, guids |
| `add_custom_input` | Add input pin to Custom expression | material_path, guid, input_name |
| `add_custom_output` | Add output pin to Custom expression | material_path, guid, output_name, output_type |
| `batch` | Execute multiple operations atomically | material_path, operations[] |

---

## 필수 워크플로우 (반드시 이 순서를 따를 것)

### 1. 구조 분석
- **get_graph_as_hlsl** 호출 -> GUID 주석 포함 pseudo-HLSL로 노드 구조 파악
- 각 줄의 `[GUID:...]` 주석으로 수정 대상 노드 식별

### 2. 동작 검증
- **get_compiled_hlsl** 호출 -> 엔진이 생성한 실제 HLSL로 계산 로직 정확히 확인
- **중요: 결과가 ~650KB로 매우 크므로 `CalcPixelMaterialInputs()` 함수만 먼저 확인할 것**
  - 이 함수 안에 모든 노드 연산이 `LocalN` 변수 체인으로 펼쳐지고, 마지막에 `PixelMaterialInputs.BaseColor = ...` 등으로 할당됨
  - `GetMaterialWorldPositionOffset()` — WPO 분석 시에만 확인
  - `CalcMaterialCustomData()` — CustomData (ClearCoat 등) 분석 시에만 확인
  - 그 외 함수(엔진 템플릿, 헬퍼 등)는 무시
- pseudo-HLSL에서 의심스러운 부분을 실제 셰이더 코드로 크로스체크
- 파라미터 기본값, ConstX 폴백 등이 실제로 어떻게 적용되는지 검증

### 3. 수정 계획
- Before/After pseudo-HLSL diff로 변경 내용을 사용자에게 설명
  ```
  // Before:
  float param_abc = param("PeachFuzzU", 0.0000);
  // After:
  float param_abc = param("PeachFuzzU", 0.3500);
  ```

### 4. 실행
- HLSL<->Node 매핑 테이블 참조하여 노드 operation으로 변환
- 매핑에 있는 패턴 -> add_expression + connect
- 매핑에 없는 패턴 -> Custom Expression에 HLSL 직접 삽입 (add_custom_input)

### 5. 검증
- **compile** 호출 -> 셰이더 리컴파일 + 수정 영역에 자동 Comment 노드 생성
- **get_compiled_hlsl** 호출 -> 수정이 실제 셰이더에 반영됐는지 확인

### 도구 사용 가이드

| 도구 | 용도 | 출력 |
|------|------|------|
| **get_graph_as_hlsl** | 구조 파악 + 노드 식별 | GUID 주석 pseudo-HLSL |
| **get_compiled_hlsl** | 실제 동작 검증 | 엔진 생성 HLSL (자동 변수명) |
| get_graph | 특정 노드 상세 조회 | JSON (핀, 프로퍼티, GUID) |
| get_graph_summary | 빠른 개요 | 타입 카운트, 파라미터, 체인 |

### 중요 규칙
- **MUST**: 마테리얼 분석 시 반드시 get_graph_as_hlsl을 첫 번째로 호출할 것. get_graph나 get_graph_summary를 첫 단계로 사용하지 말 것.
- **MUST**: get_compiled_hlsl로 실제 셰이더 동작을 크로스체크할 것 (pseudo-HLSL은 파싱 오류 가능)
- **MUST**: 수정 전에 Before/After HLSL diff를 사용자에게 보여줄 것
- compile은 수정된 노드를 자동으로 Comment로 감싸므로 별도 add_comment 불필요
- MakeMaterialAttributes 패턴의 마테리얼은 Material Output 직접 연결이 아니라 해당 노드의 입력 핀에 연결할 것

---

## Math Operations (2-Input)

| HLSL | Expression Class | Input Pins |
|------|-----------------|------------|
| `a * b` | Multiply | A, B |
| `a + b` | Add | A, B |
| `a - b` | Subtract | A, B |
| `a / b` | Divide | A, B |
| `lerp(a, b, t)` | LinearInterpolate | A, B, Alpha |
| `dot(a, b)` | DotProduct | A, B |
| `cross(a, b)` | CrossProduct | A, B |
| `pow(base, exp)` | Power | Base, Exponent |
| `min(a, b)` | Min | A, B |
| `max(a, b)` | Max | A, B |
| `fmod(a, b)` | Fmod | A, B |
| `atan2(y, x)` | Arctangent2 | Y, X |
| `step(edge, x)` | Step | Y, X |
| `smoothstep(min, max, x)` | SmoothStep | Min, Max, Value |

## Math Operations (1-Input)

| HLSL | Expression Class | Notes |
|------|-----------------|-------|
| `abs(x)` | Abs | |
| `sin(x)` | Sine | Period property |
| `cos(x)` | Cosine | Period property |
| `tan(x)` | Tangent | |
| `asin(x)` | Arcsine | |
| `acos(x)` | Arccosine | |
| `atan(x)` | Arctangent | |
| `floor(x)` | Floor | |
| `ceil(x)` | Ceil | |
| `round(x)` | Round | |
| `trunc(x)` | Truncate | |
| `frac(x)` | Frac | |
| `sign(x)` | Sign | |
| `sqrt(x)` | SquareRoot | |
| `exp(x)` | Exponential | |
| `exp2(x)` | Exponential2 | |
| `log(x)` | Logarithm | |
| `log2(x)` | Logarithm2 | |
| `log10(x)` | Logarithm10 | |
| `saturate(x)` | Saturate | clamp(x, 0, 1) |
| `1.0 - x` | OneMinus | |
| `normalize(v)` | Normalize | |
| `length(v)` | Length | |

## Constants & Parameters

| Purpose | Expression Class | Key Properties |
|---------|-----------------|---------------|
| `float(x)` | Constant | R |
| `float2(x,y)` | Constant2Vector | R, G |
| `float3(r,g,b)` | Constant3Vector | Constant (FLinearColor) |
| `float4(r,g,b,a)` | Constant4Vector | Constant (FLinearColor) |
| Scalar parameter | ScalarParameter | ParameterName, DefaultValue |
| Vector parameter | VectorParameter | ParameterName, DefaultValue |
| Static switch | StaticSwitchParameter | ParameterName, DefaultValue |

## Texture Sampling

| Purpose | Expression Class | Input Pins | Notes |
|---------|-----------------|------------|-------|
| `tex2D(tex, uv)` | TextureSample | UVs | Texture set via property |
| Texture parameter | TextureSampleParameter2D | UVs | MI overridable |
| Cubemap | TextureSampleParameterCube | UVs | |
| Texture object | TextureObject | — | Reference only (no sampling) |

## Vector Operations

| Purpose | Expression Class | Input Pins |
|---------|-----------------|------------|
| swizzle (.rgb, .rg) | ComponentMask | Input (R,G,B,A bool properties) |
| Vector combine | AppendVector | A, B |
| Break attributes | BreakMaterialAttributes | Input |

## World/Camera/Object (no inputs)

| Purpose | Expression Class |
|---------|-----------------|
| World position | WorldPosition |
| Object position | ObjectPositionWS |
| Camera position | CameraPositionWS |
| Vertex normal | VertexNormalWS |
| Pixel normal | PixelNormalWS |
| Texture coordinate | TextureCoordinate |
| Time | Time |
| Screen position | ScreenPosition |

## Material Attributes

| Purpose | Expression Class |
|---------|-----------------|
| Combine attributes | MakeMaterialAttributes |
| Break attributes | BreakMaterialAttributes |
| Set attributes | SetMaterialAttributes |

## Common Patterns (composite node combinations)

| Pattern | HLSL | Node | Inputs/Properties |
|---------|------|------|-------------------|
| Fresnel | `pow(1-saturate(dot(N,V)), exp)` | Fresnel | ExponentIn, BaseReflectFractionIn |
| UV Panning | `uv + time * speed` | Panner | Coordinate, Time / SpeedX, SpeedY props |
| Desaturation | `dot(color, luminance)` | Desaturation | Input, Fraction |
| Normal Unpack | `n * 2.0 - 1.0` | TextureSample | Sampler Type = Normal |
| Clamp | `clamp(x, min, max)` | Clamp | Input, Min, Max |
| Conditional | `x > y ? a : b` | If | A, B (compare), A>B, A==B, A<B (results) |
| Noise | `noise(uv)` | Noise | Position / FilterWidth, OutputMin, OutputMax props |

## Custom Expression (unmapped HLSL)

For functions/patterns not in the tables above, use Custom Expression:

```json
// 1. Add Custom expression
{"operation": "add_expression", "expression_class": "Custom", "properties": {
  "Code": "return saturate(MyInput * 2.0 - 0.5);",
  "OutputType": "CMOT_Float3",
  "Description": "Custom Transform"
}}

// 2. Add input pin
{"operation": "add_custom_input", "guid": "<custom_guid>", "input_name": "MyInput"}

// 3. Connect source to custom input
{"operation": "connect", "source_guid": "<src>", "source_pin": "Output", "dest_guid": "<custom_guid>", "dest_pin": "MyInput"}
```

Reference input pins by name in Code: `return MyInput * 2.0;`

Multiple outputs:
```json
// Add named output
{"operation": "add_custom_output", "guid": "<custom_guid>", "output_name": "NormalOut", "output_type": "Float3"}
// In Code: NormalOut = ...; (return is the primary output)
```
