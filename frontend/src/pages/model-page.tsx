import { useQuery } from '@tanstack/react-query'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { api } from '../lib/api'
import { REGION_COLORS, toTitleCase } from '../lib/format'
import { ErrorState, LoadingState } from '../components/loading-state'
import { Card, Eyebrow, MetricCard, SectionCopy, SectionTitle } from '../components/ui'

export function ModelPage() {
  const modelQuery = useQuery({
    queryKey: ['model-info'],
    queryFn: api.fetchModelInfo,
    staleTime: 5 * 60_000,
  })

  if (modelQuery.isLoading) return <LoadingState label="Loading model diagnostics…" />
  if (modelQuery.error) return <ErrorState error={modelQuery.error as Error} />
  if (!modelQuery.data) return null

  const model = modelQuery.data
  const featureData = Object.entries(model.feature_importance)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, value]) => ({ name: toTitleCase(name), value }))

  const compareData = [
    { name: 'Random Forest', value: model.metrics.rf.r2, fill: '#f26b3a' },
    { name: 'Linear Regression', value: model.metrics.lr.r2, fill: '#d1c4ba' },
    { name: 'Gradient Boosting', value: model.metrics.gbm.r2, fill: '#8a6b58' },
  ]

  return (
    <div className="space-y-8">
      <div className="space-y-5">
        <Eyebrow>Method and diagnostics</Eyebrow>
        <SectionTitle accent="made legible.">Inspect the model without losing the product feel</SectionTitle>
        <SectionCopy>
          The methodology page keeps the analytical depth, but presents it with the same editorial calm as the rest
          of the application.
        </SectionCopy>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Target" value="WHO modeled" supporting={model.target_display} />
        <MetricCard label="Training period" value={model.training_period} supporting="Temporal train window" />
        <MetricCard label="Test period" value={model.test_period} supporting="Held-out evaluation window" />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="p-6">
          <Eyebrow>Model comparison</Eyebrow>
          <div className="mt-2 font-display text-3xl text-charcoal">Held-out R²</div>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={compareData}>
                <CartesianGrid vertical={false} stroke="#efe4dc" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[14, 14, 6, 6]}>
                  {compareData.map((entry) => (
                    <Cell key={entry.name} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <Eyebrow>Importance</Eyebrow>
          <div className="mt-2 font-display text-3xl text-charcoal">What drives the model</div>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={featureData} layout="vertical">
                <CartesianGrid horizontal stroke="#efe4dc" />
                <XAxis type="number" axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} width={120} />
                <Tooltip />
                <Bar dataKey="value" fill="#f26b3a" radius={[0, 12, 12, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="p-6">
          <Eyebrow>Residuals by region</Eyebrow>
          <div className="mt-2 font-display text-3xl text-charcoal">Regional error profile</div>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={model.diagnostics.by_region}>
                <CartesianGrid vertical={false} stroke="#efe4dc" />
                <XAxis dataKey="region" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="mae" fill="#f26b3a" radius={[12, 12, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <Eyebrow>Predicted vs actual</Eyebrow>
          <div className="mt-2 font-display text-3xl text-charcoal">Held-out scatter sample</div>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid stroke="#efe4dc" />
                <XAxis dataKey="actual" name="Actual" axisLine={false} tickLine={false} />
                <YAxis dataKey="predicted" name="Predicted" axisLine={false} tickLine={false} />
                <Tooltip cursor={{ strokeDasharray: '4 4' }} />
                <Scatter
                  data={model.diagnostics.scatter_sample}
                  shape={(props) => {
                    const { cx, cy, payload } = props
                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={5.5}
                        fill={REGION_COLORS[payload.region] ?? '#f26b3a'}
                        fillOpacity={0.82}
                        stroke="#fffaf5"
                        strokeWidth={1}
                      />
                    )
                  }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <Eyebrow>Cross-validation configuration</Eyebrow>
        <div className="mt-2 font-display text-3xl text-charcoal">Best tuned random forest settings</div>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <div className="rounded-[1.5rem] bg-surface-2 p-5 text-sm leading-7 text-charcoal/70">
            <div>Best CV score ({model.metrics.rf_cv_scoring}): {model.metrics.rf_cv_best_score.toFixed(3)}</div>
            <div>Train rows: {model.metrics.train_rows.toLocaleString()}</div>
            <div>Test rows: {model.metrics.test_rows.toLocaleString()}</div>
            <div>Target transform: {model.metrics.target_transform}</div>
          </div>
          <pre className="overflow-auto rounded-[1.5rem] bg-charcoal px-5 py-4 text-sm leading-7 text-ivory">
            {JSON.stringify(model.metrics.rf_best_params, null, 2)}
          </pre>
        </div>
      </Card>

      <Card className="p-6">
        <Eyebrow>Model card</Eyebrow>
        <div className="mt-2 font-display text-3xl text-charcoal">Intended use and limitations</div>
        <pre className="mt-5 overflow-auto whitespace-pre-wrap rounded-[1.5rem] bg-[#f8f2ec] p-6 text-sm leading-7 text-charcoal/74">
          {model.model_card}
        </pre>
      </Card>
    </div>
  )
}
