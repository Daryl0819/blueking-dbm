# -*- coding: utf-8 -*-
"""
TencentBlueKing is pleased to support the open source community by making 蓝鲸智云-DB管理系统(BlueKing-BK-DBM) available.
Copyright (C) 2017-2023 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at https://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
import re

from django.utils.translation import ugettext as _
from rest_framework import serializers

from backend.db_meta.enums import ClusterType
from backend.db_meta.models import Cluster
from backend.ticket.builders.mysql.mysql_partition import PartitionObjectSerializer

from . import mock


class PartitionListSerializer(serializers.Serializer):
    bk_biz_id = serializers.IntegerField(help_text=_("业务ID"))
    cluster_type = serializers.ChoiceField(help_text=_("集群类型"), choices=ClusterType.get_choices())
    immute_domains = serializers.ListField(help_text=_("集群域名"), child=serializers.CharField(), required=False)
    dblikes = serializers.ListField(help_text=_("匹配库"), child=serializers.CharField(), required=False)
    tblikes = serializers.ListField(help_text=_("匹配表"), child=serializers.CharField(), required=False)

    limit = serializers.IntegerField(required=False, default=10)
    offset = serializers.IntegerField(required=False, default=0)


class PartitionListResponseSerializer(serializers.Serializer):
    class Meta:
        swagger_schema_fields = {"example": mock.PARTITION_LIST_DATA}


class PartitionDeleteSerializer(serializers.Serializer):
    bk_biz_id = serializers.IntegerField(help_text=_("业务ID"))
    cluster_type = serializers.ChoiceField(help_text=_("集群类型"), choices=ClusterType.get_choices())
    ids = serializers.ListField(help_text=_("分区策略ID"), child=serializers.IntegerField())


class PartitionCreateSerializer(serializers.Serializer):
    bk_biz_id = serializers.IntegerField(help_text=_("业务ID"))
    bk_cloud_id = serializers.IntegerField(help_text=_("云区域ID"))
    cluster_type = serializers.ChoiceField(help_text=_("集群类型"), choices=ClusterType.get_choices())
    immute_domain = serializers.CharField(help_text=_("集群域名"))
    cluster_id = serializers.IntegerField(help_text=_("集群ID"))
    dblikes = serializers.ListField(help_text=_("匹配库列表(支持通配)"), child=serializers.CharField())
    tblikes = serializers.ListField(help_text=_("匹配表列表(不支持通配)"), child=serializers.CharField())
    partition_column = serializers.CharField(help_text=_("分区字段"))
    partition_column_type = serializers.CharField(help_text=_("分区字段类型"))
    expire_time = serializers.IntegerField(help_text=_("过期时间"))
    partition_time_interval = serializers.IntegerField(help_text=_("分区间隔"))
    port = serializers.SerializerMethodField(help_text=_("PORT"))
    creator = serializers.SerializerMethodField(help_text=_("创建者"))
    updator = serializers.SerializerMethodField(help_text=_("更新者"))

    def get_port(self, obj):
        return Cluster.objects.get(id=obj["cluster_id"]).get_partition_port()

    def get_creator(self, obj):
        return self.context["request"].user.username

    def get_updator(self, obj):
        return self.context["request"].user.username

    def validate(self, attrs):
        # 表不支持通配
        for tb in attrs["tblikes"]:
            if "%" in tb or "*" in tb:
                raise serializers.ValidationError(_("分区表不支持通配"))

        return attrs


class PartitionUpdateSerializer(PartitionCreateSerializer):
    pass


class PartitionDisableSerializer(serializers.Serializer):
    cluster_type = serializers.ChoiceField(help_text=_("集群类型"), choices=ClusterType.get_choices())
    operator = serializers.SerializerMethodField(help_text=_("操作者"))
    ids = serializers.ListField(help_text=_("分区策略ID"), child=serializers.IntegerField())

    def get_operator(self, obj):
        return self.context["request"].user.username


class PartitionEnableSerializer(PartitionDisableSerializer):
    pass


class PartitionLogSerializer(serializers.Serializer):
    cluster_type = serializers.ChoiceField(help_text=_("集群类型"), choices=ClusterType.get_choices())
    config_id = serializers.IntegerField(help_text=_("分区策略ID"))

    limit = serializers.IntegerField(required=False, default=10)
    offset = serializers.IntegerField(required=False, default=0)


class PartitionLogResponseSerializer(serializers.Serializer):
    class Meta:
        swagger_schema_fields = {"example": mock.PARTITION_LOG_DATA}


class PartitionDryRunSerializer(serializers.Serializer):
    cluster_type = serializers.ChoiceField(help_text=_("集群类型"), choices=ClusterType.get_choices())
    bk_biz_id = serializers.IntegerField(help_text=_("业务ID"))
    config_id = serializers.IntegerField(help_text=_("分区配置ID"))
    cluster_id = serializers.IntegerField(help_text=_("集群ID"))
    immute_domain = serializers.CharField(help_text=_("集群域名"))
    port = serializers.SerializerMethodField(help_text=_("PORT"))
    bk_cloud_id = serializers.IntegerField(help_text=_("云区域ID"))

    def get_port(self, obj):
        return Cluster.objects.get(id=obj["cluster_id"]).get_partition_port()


class PartitionDryRunResponseSerializer(serializers.Serializer):
    class Meta:
        swagger_schema_fields = {"example": mock.PARTITION_DRY_RUN_DATA}


class PartitionRunSerializer(serializers.Serializer):
    bk_biz_id = serializers.IntegerField(help_text=_("业务ID"))
    cluster_id = serializers.IntegerField(help_text=_("集群ID"))
    bk_cloud_id = serializers.IntegerField(help_text=_("云区域ID"))
    immute_domain = serializers.CharField(help_text=_("集群域名"))
    partition_objects = serializers.DictField(
        help_text=_("分区执行对象列表"), child=serializers.ListSerializer(child=PartitionObjectSerializer())
    )


class PartitionColumnVerifySerializer(serializers.Serializer):
    bk_biz_id = serializers.IntegerField(help_text=_("业务ID"))
    cluster_id = serializers.IntegerField(help_text=_("云区域ID"))
    dblikes = serializers.ListField(help_text=_("匹配库列表(支持通配)"), child=serializers.CharField())
    tblikes = serializers.ListField(help_text=_("匹配表列表(不支持通配)"), child=serializers.CharField())
    partition_column = serializers.CharField(help_text=_("分区字段"))
    partition_column_type = serializers.CharField(help_text=_("分区字段类型"))

    def validate(self, attrs):
        # 校验库表不能包含特殊字符  防止SQL注入
        special_pattern = re.compile(r"[￥$!@#^&*()+={}\[\];:'\"<>,.?/\\| ]")
        for check_str in [*attrs["dblikes"], *attrs["tblikes"]]:
            if special_pattern.findall(check_str):
                raise serializers.ValidationError(_("【{}】请不要库表匹配中包含特殊字符！").format(check_str))


class PartitionColumnVerifyResponseSerializer(serializers.Serializer):
    class Meta:
        swagger_schema_fields = {"example": mock.PARTITION_FIELD_VERIFY_DATA}
