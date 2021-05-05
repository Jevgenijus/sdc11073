from ..namespaces import domTag
from .. import sdcdevice
from .. import pmtypes
from ..nomenclature import NomenclatureCodes as nc

from . import providerbase


# coded values for SDC audio pause
MDC_OP_SET_ALL_ALARMS_AUDIO_PAUSE = pmtypes.CodedValue(nc.MDC_OP_SET_ALL_ALARMS_AUDIO_PAUSE)
MDC_OP_SET_CANCEL_ALARMS_AUDIO_PAUSE = pmtypes.CodedValue(nc.MDC_OP_SET_CANCEL_ALARMS_AUDIO_PAUSE)

class GenericSDCAudioPauseProvider(providerbase.ProviderRole):
    """Handling of global audio pause.
    It guarantees that there are operations with codes "MDC_OP_SET_ALL_ALARMS_AUDIO_PAUSE"
    and "MDC_OP_SET_CANCEL_ALARMS_AUDIO_PAUSE".
    """
    def __init__(self, log_prefix):
        super(GenericSDCAudioPauseProvider, self).__init__(log_prefix)
        self._setGlobalAudioPauseOperations = []
        self._cancelGlobalAudioPauseOperations = []

    def makeOperationInstance(self, operationDescriptorContainer):
        if operationDescriptorContainer.coding == MDC_OP_SET_ALL_ALARMS_AUDIO_PAUSE.coding:
            self._logger.info('instantiating "set audio pause" operation from existing descriptor handle={}'.format(operationDescriptorContainer.handle))
            set_ap_operation = self._mkOperationFromOperationDescriptor(operationDescriptorContainer,
                                                                        currentRequestHandler=self._setGlobalAudioPause)
            self._setGlobalAudioPauseOperations.append(set_ap_operation)
            return set_ap_operation

        elif operationDescriptorContainer.coding == MDC_OP_SET_CANCEL_ALARMS_AUDIO_PAUSE.coding:
            self._logger.info('instantiating "cancel audio pause" operation from existing descriptor handle={}'.format(operationDescriptorContainer.handle))
            cancel_ap_operation = self._mkOperationFromOperationDescriptor(operationDescriptorContainer,
                                                                           currentRequestHandler=self._cancelGlobalAudioPause)

            self._cancelGlobalAudioPauseOperations.append(cancel_ap_operation)
            return cancel_ap_operation
        return None


    def makeMissingOperations(self):
        ops = []
        operationTargetContainer = self._mdib.descriptions.NODETYPE.getOne(
            domTag('MdsDescriptor'))  # the operation target is the mds itself
        if not self._setGlobalAudioPauseOperations:
            self._logger.info('adding "set audio pause" operation, no descriptor in mdib (looked for code = {})'.format(
                nc.MDC_OP_SET_ALL_ALARMS_AUDIO_PAUSE))
            set_ap_operation = self._mkOperation(sdcdevice.sco.ActivateOperation,
                                                 handle='AP__ON',
                                                 operationTargetHandle=operationTargetContainer.handle,
                                                 codedValue=MDC_OP_SET_ALL_ALARMS_AUDIO_PAUSE,
                                                 currentRequestHandler=self._setGlobalAudioPause)
            self._setGlobalAudioPauseOperations.append(set_ap_operation)
            ops.append(set_ap_operation)
        if not self._cancelGlobalAudioPauseOperations:
            self._logger.info(
                'adding "cancel audio pause" operation, no descriptor in mdib (looked for code = {})'.format(
                    nc.MDC_OP_SET_CANCEL_ALARMS_AUDIO_PAUSE))
            cancel_ap_operation = self._mkOperation(sdcdevice.sco.ActivateOperation,
                                                    handle='AP__CANCEL',
                                                    operationTargetHandle=operationTargetContainer.handle,
                                                    codedValue=MDC_OP_SET_CANCEL_ALARMS_AUDIO_PAUSE,
                                                    currentRequestHandler=self._cancelGlobalAudioPause)
            ops.append(cancel_ap_operation)
            self._setGlobalAudioPauseOperations.append(cancel_ap_operation)
        return ops


    def _setGlobalAudioPause(self, operationInstance, request):  # pylint: disable=unused-argument
        ''' This is the code that executes the operation itself:
        SF1132: If global audio pause is initiated, all SystemSignalActivation/State for all alarm systems of the
        product with SystemSignalActivation/Manifestation evaluating to 'Aud' shall be set to 'Psd'.

        SF958: If signal pause is initiated for an alert signal that is not an ACKNOWLEDGE CAPABLE ALERT SIGNAL,
        then the Alert Provider shall set the AlertSignalState/ActivationState to 'Psd' and the AlertSignalState/Presence to 'Off'.

        SF959: If signal pause is initiated for an ACKNOWLEDGEABLE ALERT SIGNAL, the the Alert Provider shall set the
        AlertSignalState/ActivationState to 'Psd' and AlertSignalState/Presence to 'Ack' for that ALERT SIGNAL.
         '''
        alertSystemDescriptors = self._mdib.descriptions.NODETYPE.get(domTag('AlertSystemDescriptor'))
        if alertSystemDescriptors is None:
            self._logger.error('SDC_SetAudioPauseOperation called, but no AlertSystemDescriptor in mdib found')
            return
        with self._mdib.mdibUpdateTransaction() as tr:
            for alertSystemDescriptor in alertSystemDescriptors:
                alertSystemState = tr.getAlertState(alertSystemDescriptor.handle)
                if alertSystemState.ActivationState != pmtypes.AlertActivation.ON:
                    self._logger.info('SDC_SetAudioPauseOperation: nothing to do')
                    tr.ungetState(alertSystemState)
                else:
                    audible_signals = [ ssa for ssa in alertSystemState.SystemSignalActivation if ssa.Manifestation == pmtypes.AlertSignalManifestation.AUD]
                    active_audible_signals = [ ssa for ssa in audible_signals if ssa.State != pmtypes.AlertActivation.PAUSED]
                    if not active_audible_signals:
                        # Alert System has no audible SystemSignalActivations, no action required
                        tr.ungetState(alertSystemState)
                    else:
                        for ssa in active_audible_signals:
                            ssa.State = pmtypes.AlertActivation.PAUSED # SF1132
                        self._logger.info('SDC_SetAudioPauseOperation: set alertsystem "{}" to paused'.format(
                            alertSystemDescriptor.handle))
                        # handle all audible alert signals of this alert system
                        allAlertSignalDescriptors = self._mdib.descriptions.NODETYPE.get(domTag('AlertSignalDescriptor'), [])
                        childAlertSignalDescriptors = [ d for d in allAlertSignalDescriptors if d.parentHandle == alertSystemDescriptor.handle]
                        audibleChildAlertSignalDescriptors = [ d for d in childAlertSignalDescriptors if d.Manifestation == pmtypes.AlertSignalManifestation.AUD]
                        for sd in audibleChildAlertSignalDescriptors:
                            alertSignalState = tr.getAlertState(sd.handle)
                            if sd.AcknowledgementSupported: #SF959
                                if alertSignalState.ActivationState != pmtypes.AlertActivation.PAUSED \
                                    or alertSignalState.Presence != pmtypes.AlertSignalPresence.ACK:
                                    alertSignalState.ActivationState = pmtypes.AlertActivation.PAUSED
                                    alertSignalState.Presence = pmtypes.AlertSignalPresence.ACK
                                else:
                                    tr.ungetState(alertSignalState)
                            else: #SF958
                                if alertSignalState.ActivationState != pmtypes.AlertActivation.PAUSED \
                                    or alertSignalState.Presence != pmtypes.AlertSignalPresence.OFF:
                                    alertSignalState.ActivationState = pmtypes.AlertActivation.PAUSED
                                    alertSignalState.Presence = pmtypes.AlertSignalPresence.OFF
                                else:
                                    tr.ungetState(alertSignalState)


    def _cancelGlobalAudioPause(self, operationInstance, request): #pylint: disable=unused-argument
        ''' This is the code that executes the operation itself:
        If global audio pause is initiated, all SystemSignalActivation/State for all alarm systems of the product with
        SystemSignalActivation/Manifestation evaluating to 'Aud' shall be set to 'Psd'.
         '''
        alertSystemDescriptors = self._mdib.descriptions.NODETYPE.get(domTag('AlertSystemDescriptor'))
        with self._mdib.mdibUpdateTransaction() as tr:
            for alertSystemDescriptor in alertSystemDescriptors:
                alertSystemState = tr.getAlertState(alertSystemDescriptor.handle)
                if alertSystemState.ActivationState != pmtypes.AlertActivation.ON:
                    self._logger.info('SDC_CancelAudioPauseOperation: nothing to do')
                    tr.ungetState(alertSystemState)
                else:
                    audible_signals = [ ssa for ssa in alertSystemState.SystemSignalActivation if ssa.Manifestation == pmtypes.AlertSignalManifestation.AUD]
                    paused_audible_signals = [ ssa for ssa in audible_signals if ssa.State == pmtypes.AlertActivation.PAUSED]
                    if not paused_audible_signals:
                        tr.ungetState(alertSystemState)
                    else:
                        for ssa in paused_audible_signals:
                            ssa.State = pmtypes.AlertActivation.ON
                        self._logger.info('SDC_SetAudioPauseOperation: set alertsystem "{}" to ON'.format(
                            alertSystemDescriptor.handle))
                        # handle all audible alert signals of this alert system
                        allAlertSignalDescriptors = self._mdib.descriptions.NODETYPE.get(domTag('AlertSignalDescriptor'), [])
                        childAlertSignalDescriptors = [ d for d in allAlertSignalDescriptors if d.parentHandle == alertSystemDescriptor.handle]
                        audibleChildAlertSignalDescriptors = [ d for d in childAlertSignalDescriptors if d.Manifestation == pmtypes.AlertSignalManifestation.AUD]
                        for sd in audibleChildAlertSignalDescriptors:
                            alertSignalState = tr.getAlertState(sd.handle)
                            alertConditionState = self._mdib.states.descriptorHandle.getOne(sd.ConditionSignaled)
                            if alertConditionState.Presence:
                                # set signal back to 'ON'
                                if alertSignalState.ActivationState == pmtypes.AlertActivation.PAUSED:
                                    alertSignalState.ActivationState = pmtypes.AlertActivation.ON
                                    alertSignalState.Presence = pmtypes.AlertSignalPresence.ON
                                else:
                                    tr.ungetState(alertSignalState)
