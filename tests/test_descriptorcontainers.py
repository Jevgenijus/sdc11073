import unittest
from lxml import etree as etree_
from sdc11073.mdib import descriptorcontainers
from sdc11073 import namespaces
from sdc11073 import pmtypes
from sdc11073 import msgtypes

test_tag = namespaces.domTag('MyDescriptor')


class TestDescriptorContainers(unittest.TestCase):

    def setUp(self):
        self.nsmapper = namespaces.DocNamespaceHelper()

    def test_AbstractDescriptorContainer(self):
        dc = descriptorcontainers.AbstractDescriptorContainer(nsmapper=self.nsmapper,
                                                              handle='123',
                                                              parent_handle='456',
                                                              )

        self.assertEqual(dc.DescriptorVersion, 0)
        self.assertEqual(dc.SafetyClassification, 'Inf')
        self.assertEqual(dc.get_actual_value('SafetyClassification'), None)
        self.assertEqual(dc.Type, None)
        self.assertEqual(dc.Extension, None)

        # test creation from node
        node = dc.mk_node(test_tag)
        dc2 = descriptorcontainers.AbstractDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                        node=node,
                                                                        parent_handle='467')
        self.assertEqual(dc2.DescriptorVersion, 0)
        self.assertEqual(dc2.SafetyClassification, 'Inf')
        self.assertEqual(dc.Type, None)
        self.assertEqual(dc.Extension, None)

        # test update from node
        dc.DescriptorVersion = 42
        dc.SafetyClassification = pmtypes.SafetyClassification.MED_A
        dc.Type = pmtypes.CodedValue('abc', 'def')

        ext_node = etree_.Element(namespaces.msgTag('Whatever'))
        etree_.SubElement(ext_node, 'foo', attrib={'someattr': 'somevalue'})
        etree_.SubElement(ext_node, 'bar', attrib={'anotherattr': 'differentvalue'})
        dc.Extension.value[namespaces.msgTag('Whatever')] = ext_node
        retrievability = msgtypes.Retrievability([msgtypes.RetrievabilityInfo(msgtypes.RetrievabilityMethod.GET),
                                                  msgtypes.RetrievabilityInfo(msgtypes.RetrievabilityMethod.PERIODIC,
                                                                              update_period=42.0),
                                                  ],
                                                 )
        dc.retrievability = retrievability
        dc2.update_from_other_container(dc)
        self.assertEqual(dc2.DescriptorVersion, 42)
        self.assertEqual(dc2.SafetyClassification, 'MedA')
        self.assertEqual(dc2.Type, dc.Type)
        self.assertEqual(dc.code_id, 'abc')
        self.assertEqual(dc.coding_system, 'def')
        self.assertEqual(dc2.Extension.value[namespaces.msgTag('Whatever')], ext_node)
        self.assertEqual(dc2.Extension.value[namespaces.msgTag('Retrievability')], retrievability)
        self.assertEqual(dc2.retrievability, retrievability)

        node = dc.mk_node(test_tag)
        dc3 = descriptorcontainers.AbstractDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                        node=node,
                                                                        parent_handle='467')
        self.assertEqual(dc3.DescriptorVersion, 42)
        self.assertEqual(dc3.SafetyClassification, 'MedA')
        self.assertEqual(dc3.Type, dc.Type)
        self.assertEqual(dc3.code_id, 'abc')
        self.assertEqual(dc3.coding_system, 'def')
        self.assertEqual(dc3.Extension.value[namespaces.msgTag('Whatever')].tag, ext_node.tag)
        self.assertEqual(dc3.Extension.value[namespaces.msgTag('Retrievability')], retrievability)
        self.assertEqual(dc3.retrievability, retrievability)


    def test_AbstractMetricDescriptorContainer(self):
        dc = descriptorcontainers.AbstractMetricDescriptorContainer(nsmapper=self.nsmapper,
                                                                    handle='123',
                                                                    parent_handle='456',
                                                                    )
        self.assertEqual(dc.MetricAvailability, 'Cont')  # the default value
        self.assertEqual(dc.MetricCategory, 'Unspec')  # the default value
        self.assertEqual(dc.DeterminationPeriod, None)
        self.assertEqual(dc.MaxMeasurementTime, None)
        self.assertEqual(dc.MaxDelayTime, None)

        # test creation from node
        node = dc.mk_node(test_tag)
        dc2 = descriptorcontainers.AbstractMetricDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                              node=node,
                                                                              parent_handle='467')
        self.assertEqual(dc2.MetricAvailability, 'Cont')
        self.assertEqual(dc2.MetricCategory, 'Unspec')
        self.assertEqual(dc2.DeterminationPeriod, None)
        self.assertEqual(dc2.MaxMeasurementTime, None)
        self.assertEqual(dc2.MaxDelayTime, None)

        # test update from node
        dc.MetricAvailability = pmtypes.MetricAvailability.INTERMITTENT
        dc.MetricCategory = pmtypes.MetricCategory.MEASUREMENT

        dc.DeterminationPeriod = 3.5
        dc.MaxMeasurementTime = 2.1
        dc.MaxDelayTime = 4
        dc.Unit = pmtypes.CodedValue('abc', 'def')
        dc.BodySite.append(pmtypes.CodedValue('ABC', 'DEF'))
        dc.BodySite.append(pmtypes.CodedValue('GHI', 'JKL'))
        dc2.update_from_other_container(dc)

        self.assertEqual(dc2.MetricAvailability, 'Intr')
        self.assertEqual(dc2.MetricCategory, 'Msrmt')
        self.assertEqual(dc2.DeterminationPeriod, 3.5)
        self.assertEqual(dc2.MaxMeasurementTime, 2.1)
        self.assertEqual(dc2.MaxDelayTime, 4)
        self.assertEqual(dc2.Unit, dc.Unit)
        self.assertEqual(dc2.BodySite, dc.BodySite)
        self.assertEqual(dc2.BodySite, [pmtypes.CodedValue('ABC', 'DEF'), pmtypes.CodedValue('GHI', 'JKL')])

    def test_NumericMetricDescriptorContainer(self):
        dc = descriptorcontainers.NumericMetricDescriptorContainer(nsmapper=self.nsmapper,
                                                                   handle='123',
                                                                   parent_handle='456',
                                                                   )
        self.assertEqual(dc.Resolution, None)
        self.assertEqual(dc.AveragingPeriod, None)

    def test_EnumStringMetricDescriptorContainer(self):
        dc = descriptorcontainers.EnumStringMetricDescriptorContainer(nsmapper=self.nsmapper,
                                                                      handle='123',
                                                                      parent_handle='456',
                                                                      )
        dc.AllowedValue = [pmtypes.AllowedValue('abc')]

        node = dc.mk_node(test_tag)
        print(etree_.tostring(node, pretty_print=True))
        dc2 = descriptorcontainers.EnumStringMetricDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                                node=node,
                                                                                parent_handle='467')
        self.assertEqual(dc.AllowedValue, dc2.AllowedValue)

    def _cmp_AlertConditionDescriptorContainer(self, dc, dc2):
        self.assertEqual(dc.Source, dc2.Source)
        self.assertEqual(dc.CauseInfo, dc2.CauseInfo)
        self.assertEqual(dc.Kind, dc2.Kind)
        self.assertEqual(dc.Priority, dc2.Priority)

    def test_AlertConditionDescriptorContainer(self):
        dc = descriptorcontainers.AlertConditionDescriptorContainer(nsmapper=self.nsmapper,
                                                                    handle='123',
                                                                    parent_handle='456',
                                                                    )
        # create copy with default values
        node = dc.mk_node(test_tag)
        dc2 = descriptorcontainers.AlertConditionDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                              node=node,
                                                                              parent_handle='467')
        self._cmp_AlertConditionDescriptorContainer(dc, dc2)

        # set values, test updateFromNode
        dc.Source = ['A', 'B']
        dc.Cause = [pmtypes.CauseInfo(
            remedyInfo=pmtypes.RemedyInfo([pmtypes.LocalizedText('abc'), pmtypes.LocalizedText('def')]),
            descriptions=[pmtypes.LocalizedText('descr1'), pmtypes.LocalizedText('descr2')]),
                    pmtypes.CauseInfo(
                        remedyInfo=pmtypes.RemedyInfo([pmtypes.LocalizedText('123'), pmtypes.LocalizedText('456')]),
                        descriptions=[pmtypes.LocalizedText('descr1'), pmtypes.LocalizedText('descr2')])
                    ]
        dc.Kind = pmtypes.AlertConditionKind.TECHNICAL
        dc.Priority = pmtypes.AlertConditionPriority.HIGH
        node = dc.mk_node(test_tag)
        dc2.update_from_other_container(dc)
        self._cmp_AlertConditionDescriptorContainer(dc, dc2)

        # create copy with values set
        dc2 = descriptorcontainers.AlertConditionDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                              node=node,
                                                                              parent_handle='467')
        self._cmp_AlertConditionDescriptorContainer(dc, dc2)

    def _cmp_LimitAlertConditionDescriptorContainer(self, dc, dc2):
        self.assertEqual(dc.MaxLimits, dc2.MaxLimits)
        self.assertEqual(dc.AutoLimitSupported, dc2.AutoLimitSupported)
        self._cmp_AlertConditionDescriptorContainer(dc, dc2)

    def test_LimitAlertConditionDescriptorContainer(self):
        dc = descriptorcontainers.LimitAlertConditionDescriptorContainer(nsmapper=self.nsmapper,
                                                                         handle='123',
                                                                         parent_handle='456',
                                                                         )
        # create copy with default values
        node = dc.mk_node(test_tag)
        dc2 = descriptorcontainers.LimitAlertConditionDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                                   node=node,
                                                                                   parent_handle='467')
        self._cmp_LimitAlertConditionDescriptorContainer(dc, dc2)

        # set values, test updateFromNode
        dc.MaxLimits = pmtypes.Range(lower=0, upper=100, step_width=1, relative_accuracy=0.1, absolute_accuracy=0.2)
        dc.AutoLimitSupported = True
        node = dc.mk_node(test_tag)
        dc2.update_from_other_container(dc)
        self._cmp_LimitAlertConditionDescriptorContainer(dc, dc2)

        # create copy with values set
        dc2 = descriptorcontainers.LimitAlertConditionDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                                   node=node,
                                                                                   parent_handle='467')
        self._cmp_LimitAlertConditionDescriptorContainer(dc, dc2)

    def test_ActivateOperationDescriptorContainer(self):
        def _cmp_ActivateOperationDescriptorContainer(_dc, _dc2):
            self.assertIsNone(_dc.diff(_dc2))
            self.assertEqual(_dc.Argument, _dc2.Argument)
            self.assertEqual(_dc.Retriggerable, _dc2.Retriggerable)

        dc = descriptorcontainers.ActivateOperationDescriptorContainer(nsmapper=self.nsmapper,
                                                                       handle='123',
                                                                       parent_handle='456',
                                                                       )
        # create copy with default values
        node = dc.mk_node(test_tag)
        dc2 = descriptorcontainers.ActivateOperationDescriptorContainer.from_node(nsmapper=self.nsmapper,
                                                                                 node=node,
                                                                                 parent_handle='456')
        _cmp_ActivateOperationDescriptorContainer(dc, dc2)

        dc.Argument = [pmtypes.ActivateOperationDescriptorArgument(arg_name=pmtypes.CodedValue('abc', 'def'),
                                                                   arg=namespaces.domTag('blubb'))]
        dc2.update_from_other_container(dc)
        _cmp_ActivateOperationDescriptorContainer(dc, dc2)

    def test_ClockDescriptorContainer_Final(self):
        self._test_ClockDescriptorContainer(cls=descriptorcontainers.ClockDescriptorContainer)

    def _test_ClockDescriptorContainer(self, cls):
        dc = cls(nsmapper=self.nsmapper,
                 handle='123',
                 parent_handle='456',
                 )
        # create copy with default values
        node = dc.mk_node(test_tag)
        dc2 = cls.from_node(nsmapper=self.nsmapper,
                           node=node,
                           parent_handle='467')
        self.assertEqual(dc.TimeProtocol, dc2.TimeProtocol)
        self.assertEqual(dc.Resolution, dc2.Resolution)

        dc.TimeProtocol = [pmtypes.CodedValue('abc', 'def'), pmtypes.CodedValue('123', '456')]
        dc.Resolution = 3.14
        dc2.update_from_other_container(dc)
        self.assertEqual(dc.TimeProtocol, dc2.TimeProtocol)
        self.assertEqual(dc.Resolution, dc2.Resolution)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestDescriptorContainers)


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
