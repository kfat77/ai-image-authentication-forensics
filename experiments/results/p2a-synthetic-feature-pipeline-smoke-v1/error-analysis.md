# P2-A synthetic pipeline smoke: error analysis

This file is a mechanics-only fixture result. It contains no real or AI-generated images and supports no detection claim.

## logistic_regression

- `fixture-103`: label=1, score=0.437401, transformation=jpeg_q75_fixture.
- `fixture-111`: label=1, score=0.239743, transformation=none.
- `fixture-117`: label=1, score=0.042171, transformation=none.
- Fixture error slice: jpeg_q75_fixture=1, none=2.
- Interpretation limit: the inputs are synthetic numeric features, so no visual, generator, or transformation cause can be inferred from these errors.

## linear_layer

- `fixture-103`: label=1, score=0.382375, transformation=jpeg_q75_fixture.
- `fixture-111`: label=1, score=0.240075, transformation=none.
- `fixture-117`: label=1, score=0.023012, transformation=none.
- Fixture error slice: jpeg_q75_fixture=1, none=2.
- Interpretation limit: the inputs are synthetic numeric features, so no visual, generator, or transformation cause can be inferred from these errors.

## tiny_mlp

- `fixture-106`: label=0, score=0.577122, transformation=jpeg_q75_fixture.
- `fixture-100`: label=0, score=0.771201, transformation=jpeg_q75_fixture.
- `fixture-111`: label=1, score=0.161329, transformation=none.
- `fixture-107`: label=1, score=0.153889, transformation=resize_075_fixture.
- `fixture-117`: label=1, score=0.146276, transformation=none.
- Fixture error slice: jpeg_q75_fixture=2, none=2, resize_075_fixture=1.
- Interpretation limit: the inputs are synthetic numeric features, so no visual, generator, or transformation cause can be inferred from these errors.
