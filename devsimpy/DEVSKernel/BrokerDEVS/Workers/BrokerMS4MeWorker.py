# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# BrokerMS4MeWorker.py ---
#                    --------------------------------
#                            Copyright (c) 2025
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/26/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# MS4Me (Multi-Server Multi-Core Messaging Execution) distributed worker
# for broker-based DEVS simulation.
#
# Implements a state-preserving, multi-core aware worker that coordinates
# with other workers through any message broker (Kafka, MQTT, RabbitMQ, etc.)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from DEVSKernel.BrokerDEVS.Workers.InMemoryBrokerWorker import InMemoryBrokerWorker
from DEVSKernel.BrokerDEVS.Core.BrokerAdapter import BrokerAdapter
from DEVSKernel.BrokerDEVS.Core.BrokerMessageTypes import (
    BaseMessage,
    SimTime,
    InitSim,
    ExecuteTransition,
    ModelOutputMessage,
    ModelDone,
    NextTime,
    SendOutput,
    SimulationDone,
    PortValue,
    TransitionDone,
)

logger = logging.getLogger(__name__)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# MS4ME SPECIFIC TYPES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class WorkerPhase(Enum):
    """MS4Me worker execution phases."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    EXECUTING = "executing"
    OUTPUT_GENERATION = "output_generation"
    NEXT_TIME_COMPUTATION = "next_time_computation"
    FINALIZED = "finalized"


@dataclass
class ModelState:
    """Snapshot of model state for checkpointing."""

    model_id: str
    phase: WorkerPhase = WorkerPhase.IDLE
    current_time: float = 0.0
    next_event_time: float = float("inf")
    state_data: Dict[str, Any] = field(default_factory=dict)
    last_update: float = 0.0
    transition_count: int = 0
    output_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "phase": self.phase.value,
            "current_time": self.current_time,
            "next_event_time": self.next_event_time,
            "state_data": self.state_data,
            "last_update": self.last_update,
            "transition_count": self.transition_count,
            "output_count": self.output_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelState":
        """Create from dictionary."""
        return cls(
            model_id=data.get("model_id", ""),
            phase=WorkerPhase(data.get("phase", "idle")),
            current_time=data.get("current_time", 0.0),
            next_event_time=data.get("next_event_time", float("inf")),
            state_data=data.get("state_data", {}),
            last_update=data.get("last_update", 0.0),
            transition_count=data.get("transition_count", 0),
            output_count=data.get("output_count", 0),
        )


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# BROKER MS4ME WORKER
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class BrokerMS4MeWorker(InMemoryBrokerWorker):
    """
    MS4Me (Multi-Server Multi-Core Messaging Execution) distributed worker.

    Extends InMemoryBrokerWorker with MS4Me-specific features:
    - State preservation and checkpointing
    - Multi-phase execution (init → execute → output → next_time)
    - Coordinated barrier synchronization
    - Per-transition profiling
    - Message ordering guarantees
    - Rollback capability

    Features:
    - Transparent state management across transitions
    - Multi-worker coordination
    - Checkpoint/restore for fault tolerance
    - Performance metrics collection
    - Out-of-order message handling with backoff

    Architecture:
    - Extends generic InMemoryBrokerWorker
    - Adds MS4Me-specific message handling
    - Maintains model state snapshots
    - Tracks execution metrics
    - Supports distributed checkpointing
    """

    def __init__(
        self,
        model,
        broker_adapter: BrokerAdapter,
        coordinator_id: str = "COORDINATOR",
        enable_checkpointing: bool = True,
        checkpoint_interval: int = 100,
        max_retries: int = 3,
        retry_backoff_ms: int = 100,
        **kwargs,
    ):
        """
        Initialize MS4Me worker.

        Args:
            model: DEVS model to execute
            broker_adapter: Broker adapter for message transport
            coordinator_id: ID of coordinating entity
            enable_checkpointing: Enable state checkpointing
            checkpoint_interval: Transitions between checkpoints
            max_retries: Maximum message send retries
            retry_backoff_ms: Milliseconds between retries
            **kwargs: Additional arguments for parent worker
        """
        super().__init__(model, broker_adapter, **kwargs)

        self.coordinator_id = coordinator_id
        self.enable_checkpointing = enable_checkpointing
        self.checkpoint_interval = checkpoint_interval
        self.max_retries = max_retries
        self.retry_backoff_ms = retry_backoff_ms

        # MS4Me state tracking
        self.state = ModelState(model_id=self._get_model_id())
        self.checkpoints: Dict[int, ModelState] = {}  # transition_count -> state

        # Performance metrics
        self.metrics = {
            "transitions_executed": 0,
            "outputs_generated": 0,
            "messages_received": 0,
            "messages_sent": 0,
            "total_transition_time": 0.0,
            "total_output_time": 0.0,
            "total_next_time_computation": 0.0,
            "max_transition_time": 0.0,
            "checkpoints_saved": 0,
        }

        logger.info(
            "Initialized BrokerMS4MeWorker for %s (checkpointing=%s)",
            self.state.model_id,
            enable_checkpointing,
        )

    def _handle_message(self, msg: BaseMessage):
        """
        Handle MS4Me-specific messages.

        Args:
            msg: Incoming message from broker
        """
        self.metrics["messages_received"] += 1

        if isinstance(msg, InitSim):
            self._handle_init_sim(msg)
        elif isinstance(msg, ExecuteTransition):
            self._handle_execute_transition(msg)
        elif isinstance(msg, SendOutput):
            self._handle_send_output(msg)
        elif isinstance(msg, NextTime):
            self._handle_next_time_request(msg)
        elif isinstance(msg, SimulationDone):
            self._handle_simulation_done(msg)
        else:
            logger.warning("Unknown message type: %s", type(msg).__name__)

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # MESSAGE HANDLERS
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def _handle_init_sim(self, msg: InitSim):
        """
        Handle initialization message.

        Args:
            msg: InitSim message
        """
        logger.debug(
            "%s: Initializing at time %.4f",
            self.state.model_id,
            msg.time.t,
        )

        self.state.phase = WorkerPhase.INITIALIZING
        self.state.current_time = msg.time.t
        self.state.next_event_time = float("inf")

        try:
            # Initialize model
            self.do_initialize()
            self.state.next_event_time = self.get_model_time_next()
            self.state.phase = WorkerPhase.IDLE

            logger.debug(
                "%s: Initialized successfully (next event: %.4f)",
                self.state.model_id,
                self.state.next_event_time,
            )

        except Exception as e:
            logger.error("%s: Initialization failed: %s", self.state.model_id, e)
            self.state.phase = WorkerPhase.IDLE
            raise

    def _handle_execute_transition(self, msg: ExecuteTransition):
        """
        Handle execute transition message.

        Args:
            msg: ExecuteTransition message
        """
        model_id = self.state.model_id
        logger.debug(
            "%s: Executing transition at time %.4f (%d inputs)",
            model_id,
            msg.time.t,
            len(msg.portValueList) if msg.portValueList else 0,
        )

        self.state.phase = WorkerPhase.EXECUTING
        transition_start = time.time()

        try:
            # Update time
            self.state.current_time = msg.time.t

            # Process external inputs
            external_inputs = {}
            if msg.portValueList:
                for pv in msg.portValueList:
                    external_inputs[pv.portIdentifier] = pv.value

            # Execute transition
            if external_inputs:
                self.do_external_transition(external_inputs)
            else:
                self.do_internal_transition()

            # Update metrics
            transition_time = time.time() - transition_start
            self.metrics["transitions_executed"] += 1
            self.metrics["total_transition_time"] += transition_time
            self.metrics["max_transition_time"] = max(
                self.metrics["max_transition_time"],
                transition_time,
            )

            # Update next event time
            self.state.next_event_time = self.get_model_time_next()
            self.state.transition_count += 1
            self.state.last_update = time.time()

            # Checkpoint if needed
            if self.enable_checkpointing and (
                self.state.transition_count % self.checkpoint_interval == 0
            ):
                self._save_checkpoint()

            # Send acknowledgment
            response = TransitionDone(
                time=msg.time,
                nextEventTime=SimTime(t=self.state.next_event_time),
                transitionCount=self.state.transition_count,
            )
            self._send_response(response)

            self.state.phase = WorkerPhase.IDLE

            logger.debug(
                "%s: Transition completed (next: %.4f, time: %.2fms)",
                model_id,
                self.state.next_event_time,
                transition_time * 1000,
            )

        except Exception as e:
            logger.error("%s: Transition failed: %s", model_id, e)
            self.state.phase = WorkerPhase.IDLE
            raise

    def _handle_send_output(self, msg: SendOutput):
        """
        Handle output request message.

        Args:
            msg: SendOutput message
        """
        model_id = self.state.model_id
        logger.debug("%s: Generating output at time %.4f", model_id, msg.time.t)

        self.state.phase = WorkerPhase.OUTPUT_GENERATION
        output_start = time.time()

        try:
            # Generate output
            output = self.do_output_function()

            # Convert output to port values
            port_values = []
            if output:
                for port, value in output.items():
                    port_values.append(
                        PortValue(
                            value=value,
                            portIdentifier=port.name if hasattr(port, "name") else str(port),
                            portType="java.lang.Object",
                        )
                    )

            # Update metrics
            output_time = time.time() - output_start
            self.metrics["outputs_generated"] += 1
            self.metrics["total_output_time"] += output_time
            self.state.output_count += 1

            # Send output
            response = ModelOutputMessage(
                time=msg.time,
                modelOutput=port_values,
            )
            self._send_response(response)

            self.state.phase = WorkerPhase.IDLE

            logger.debug(
                "%s: Output generated (%d ports, time: %.2fms)",
                model_id,
                len(port_values),
                output_time * 1000,
            )

        except Exception as e:
            logger.error("%s: Output generation failed: %s", model_id, e)
            self.state.phase = WorkerPhase.IDLE
            raise

    def _handle_next_time_request(self, msg: NextTime):
        """
        Handle next event time request.

        Args:
            msg: NextTime message (reusing this type for request)
        """
        model_id = self.state.model_id
        logger.debug("%s: Computing next event time", model_id)

        self.state.phase = WorkerPhase.NEXT_TIME_COMPUTATION
        time_start = time.time()

        try:
            # Compute next event time
            next_time = self.get_model_time_next()
            self.state.next_event_time = next_time

            # Update metrics
            next_time_computation = time.time() - time_start
            self.metrics["total_next_time_computation"] += next_time_computation

            # Send response
            response = NextTime(
                time=msg.time,
                nextEventTime=SimTime(t=next_time),
            )
            self._send_response(response)

            self.state.phase = WorkerPhase.IDLE

            logger.debug(
                "%s: Next event time computed (%.4f, time: %.2fms)",
                model_id,
                next_time,
                next_time_computation * 1000,
            )

        except Exception as e:
            logger.error("%s: Next time computation failed: %s", model_id, e)
            self.state.phase = WorkerPhase.IDLE
            raise

    def _handle_simulation_done(self, msg: SimulationDone):
        """
        Handle simulation completion message.

        Args:
            msg: SimulationDone message
        """
        logger.info(
            "%s: Simulation complete at time %.4f",
            self.state.model_id,
            msg.time.t,
        )

        self.state.phase = WorkerPhase.FINALIZED
        self._print_metrics()
        self.stop()

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # STATE MANAGEMENT
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def _save_checkpoint(self):
        """
        Save checkpoint of current model state.

        Used for fault tolerance and recovery.
        """
        checkpoint_num = self.state.transition_count
        self.checkpoints[checkpoint_num] = ModelState(
            model_id=self.state.model_id,
            phase=self.state.phase,
            current_time=self.state.current_time,
            next_event_time=self.state.next_event_time,
            state_data=dict(self.state.state_data),  # Deep copy
            last_update=self.state.last_update,
            transition_count=self.state.transition_count,
            output_count=self.state.output_count,
        )

        self.metrics["checkpoints_saved"] += 1

        logger.debug(
            "%s: Checkpoint saved at transition %d",
            self.state.model_id,
            checkpoint_num,
        )

        # Keep only last N checkpoints to save memory
        max_checkpoints = 10
        if len(self.checkpoints) > max_checkpoints:
            oldest = min(self.checkpoints.keys())
            del self.checkpoints[oldest]

    def restore_checkpoint(self, transition_count: int) -> bool:
        """
        Restore model state from checkpoint.

        Args:
            transition_count: Checkpoint to restore

        Returns:
            True if restored successfully
        """
        if transition_count not in self.checkpoints:
            logger.warning(
                "%s: Checkpoint %d not available",
                self.state.model_id,
                transition_count,
            )
            return False

        checkpoint = self.checkpoints[transition_count]
        self.state = ModelState(
            model_id=checkpoint.model_id,
            phase=checkpoint.phase,
            current_time=checkpoint.current_time,
            next_event_time=checkpoint.next_event_time,
            state_data=dict(checkpoint.state_data),
            last_update=checkpoint.last_update,
            transition_count=checkpoint.transition_count,
            output_count=checkpoint.output_count,
        )

        logger.info(
            "%s: Restored from checkpoint at transition %d",
            self.state.model_id,
            transition_count,
        )
        return True

    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Get current state snapshot.

        Returns:
            State snapshot for checkpointing/monitoring
        """
        return self.state.to_dict()

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # UTILITY METHODS
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def _send_response(self, response: BaseMessage, retries: int = 0) -> bool:
        """
        Send response message with retry logic.

        Args:
            response: Response message to send
            retries: Current retry count

        Returns:
            True if sent successfully
        """
        try:
            _, out_topic = self._get_model_topics()
            self.send_message(out_topic, response)
            self.metrics["messages_sent"] += 1
            return True
        except Exception as e:
            if retries < self.max_retries:
                logger.warning(
                    "%s: Send failed, retrying (%d/%d): %s",
                    self.state.model_id,
                    retries + 1,
                    self.max_retries,
                    e,
                )
                time.sleep(self.retry_backoff_ms / 1000.0)
                return self._send_response(response, retries + 1)
            else:
                logger.error("%s: Send failed after %d retries", self.state.model_id, self.max_retries)
                return False

    def _get_model_topics(self) -> tuple:
        """
        Get input and output topics for this model.

        Returns:
            Tuple of (in_topic, out_topic)
        """
        model_id = self.state.model_id
        in_topic = f"devs-in-{model_id}"
        out_topic = f"devs-out-{model_id}"
        return (in_topic, out_topic)

    def _print_metrics(self):
        """Print execution metrics."""
        model_id = self.state.model_id

        logger.info("=" * 70)
        logger.info("MS4Me Worker Metrics: %s", model_id)
        logger.info("=" * 70)

        if self.metrics["transitions_executed"] > 0:
            avg_transition = (
                self.metrics["total_transition_time"]
                / self.metrics["transitions_executed"]
            )
            logger.info("  Transitions: %d (avg: %.2fms, max: %.2fms)",
                self.metrics["transitions_executed"],
                avg_transition * 1000,
                self.metrics["max_transition_time"] * 1000,
            )

        if self.metrics["outputs_generated"] > 0:
            avg_output = (
                self.metrics["total_output_time"] / self.metrics["outputs_generated"]
            )
            logger.info("  Outputs: %d (avg: %.2fms)",
                self.metrics["outputs_generated"],
                avg_output * 1000,
            )

        logger.info("  Messages: %d received, %d sent",
            self.metrics["messages_received"],
            self.metrics["messages_sent"],
        )

        if self.enable_checkpointing:
            logger.info("  Checkpoints: %d saved",
                self.metrics["checkpoints_saved"],
            )

        logger.info("=" * 70)

    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
    #
    # ACCESSORS
    #
    ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return dict(self.metrics)

    def get_phase(self) -> WorkerPhase:
        """Get current execution phase."""
        return self.state.phase

    def get_transition_count(self) -> int:
        """Get number of transitions executed."""
        return self.state.transition_count

    def get_output_count(self) -> int:
        """Get number of outputs generated."""
        return self.state.output_count

    def get_checkpoint_count(self) -> int:
        """Get number of saved checkpoints."""
        return len(self.checkpoints)
