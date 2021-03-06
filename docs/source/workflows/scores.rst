Scores
======

Scores rank materials according to a set of objectives and constraints.
An objective defines the goal for a scalar value associated with a particular descriptor.
The goal can be to either maximize or minimize a value by using :class:`~citrine.informatics.objectives.ScalarMaxObjective` or :class:`~citrine.informatics.objectives.ScalarMinObjective`, respectively.
Constraints represent a set of conditions on variables that should be satisfied.
Constraints can used to restrict either a design space or descriptor values in design candidates.
There are two constraint types:
:class:`~citrine.informatics.constraints.ScalarRangeConstraint` restricts a scalar value between lower and upper bounds.
:class:`~citrine.informatics.constraints.CategoricalConstraint` restricts a descriptor value to a set of acceptable values.

A candidate is scored based on the objective value and likelihood of satisfying the constraints.
Higher scores represent “better” materials.

Currently, there are two scores:

-  `Maximum expected improvement <#maximum-expected-improvement>`__
-  `Maximum likelihood of improvement <#maximum-likelihood-of-improvement>`__

Maximum expected improvement
----------------------------

Maximum expected improvement (MEI) is the magnitude of expected improvement calculated from the integral from the best training objective (i.e. baseline) to infinity of ``p(x)(x-a)``, where ``a`` is the best objective value in the training set.
:class:`~citrine.informatics.scores.MEIScore` supports 0 or 1 objective.
If no objective is provided, the score is the probability of satisfying all constraints.

MEI is calculated from two components: predicted value and uncertainty.
Higher scores result from a more optimal predicted value, higher uncertainty or both.
Higher predicted values exploit information known about the current dataset, e.g. materials of a given type are known to perform well.
Higher uncertainty leads to exploration of a design space, e.g. little is known about a certain class materials, but materials from this region of the design space could perform well.

Maximum likelihood of improvement
---------------------------------

Maximum likelihood of improvement (MLI) is the probability that a candidate satisfies a set of constraints and is an improvement over known objective values.
:class:`~citrine.informatics.scores.MLIScore` supports 0 or more objectives.
If no objectives are provided, the MLI score is 0.
When multiple objectives are present, the score is the probability of the objective that is most likely to be improved.
MLI scores are bounded by 0 and 1.

The following demonstrates how to create an MLI score and use it when triggering a design workflow:

.. code:: python

   from citrine.informatics.objectives import ScalarMaxObjective
   from citrine.informatics.scores import MLIScore

   # create an objective to maximize Shear modulus
   objective = ScalarMaxObjective(descriptor_key='Shear modulus')

   # Baseline is the highest shear modulus from the training data
   # (assumed to be 150 here)
   baseline = 150.0

   # Create an MLI score from the objective and baseline
   score = MLIScore(
       name='MLI(Shear modulus)',
       description='Experimental design score for shear modulus',
       objectives=[objective],
       baselines=[150.0]
   )

   # assuming you have a validated workflow, the score can be used a design run via:
   execution = workflow.executions.trigger(score)
